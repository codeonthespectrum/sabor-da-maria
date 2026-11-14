"""Busca de receitas reais na internet — arquitetura cascata (ADR 0004).

Nível 1 (descoberta): busca interna do site de receitas.
Nível 2 (extração):   parse determinístico do JSON-LD schema.org/Recipe.
Nível 3 (fallback):   SemJsonLd sobe para o agente, que aciona o subagente
                      Luna para extrair do HTML (ADR 0003).

A camada HTTP é propositalmente fina: toda a lógica testável vive em
extrair_receita_de_html e _parsear_linha_ingrediente.
"""

import json
import re
import urllib.request
import urllib.parse
from fractions import Fraction

SITES = [
    ("tudogostoso", "https://www.tudogostoso.com.br/busca?q={query}"),
]

_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


class SemJsonLd(RuntimeError):
    """A página não tem schema.org/Recipe utilizável — fallback para o Luna."""

    def __init__(self, mensagem: str, url: str = ""):
        super().__init__(mensagem)
        self.url = url


def extrair_texto_bruto(url: str, max_chars: int = 12000) -> str:
    """Busca a página e devolve só o texto visível, sem tags nem scripts.

    É o insumo do nível 3 da cascata: o agente passa este texto INLINE no
    contexto do subagente (Luna), que responde em 1 turno sem tools — é o
    que mantém o retorno da delegação abaixo de 5s (ver AGENTS.md)."""
    html = _get(url)
    html = re.sub(r"(?is)<(script|style|noscript|svg|header|footer|nav|form)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?s)<!--.*?-->", " ", html)
    texto = re.sub(r"(?s)<[^>]+>", "\n", html)
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n\s*\n+", "\n", texto)
    return texto.strip()[:max_chars]


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def buscar_receitas(ingredientes: list[str], max_resultados: int = 5) -> list[dict]:
    """Nível 1: busca interna do site. Retorna [{titulo, url, site}]."""
    query = urllib.parse.quote(" ".join(ingredientes))
    resultados = []
    for site, template in SITES:
        html = _get(template.format(query=query))
        # Links para páginas de receita do TudoGostoso: /receita/<id>-<slug>.html
        for href, titulo in re.findall(
            r'href="((?:https://www\.tudogostoso\.com\.br)?/receita/\d+-[^"]+\.html)"[^>]*>([^<]*)',
            html,
        ):
            url = href if href.startswith("http") else f"https://www.tudogostoso.com.br{href}"
            resultados.append({"titulo": titulo.strip(), "url": url, "site": site})
            if len(resultados) >= max_resultados:
                return resultados
    return resultados


_LINHA_RE = re.compile(
    r"^\s*(\d+(?:[.,]\d+)?(?:\s*\d+/\d+)?)\s*"          # quantidade ("2", "1/2", "1,5")
    r"((?:colher(?:es)? de (?:sopa|chá|café)|xícaras?|copos?|latas?|caixas?|pacotes?|"
    r"gramas?|quilos?|kg|g|ml|l|litros?|dentes?|folhas?|pitadas?|maços?|unidades?)\b)?"
    r"\s*(?:de\s+)?(.*)$",
    re.IGNORECASE,
)


def _parsear_linha_ingrediente(linha: str) -> dict:
    """"600 g de peito de frango" -> {nome, quantidade, unidade}.
    "Sal a gosto" -> {nome, quantidade: None, unidade: None}."""
    m = _LINHA_RE.match(linha.strip())
    if not m:
        return {"nome": linha.strip(), "quantidade": None, "unidade": None}
    qtd_txt, unidade, nome = m.groups()
    quantidade = None
    if qtd_txt:
        qtd_txt = qtd_txt.strip().replace(",", ".")
        if " " in qtd_txt:  # "1 1/2"
            inteiro, frac = qtd_txt.split()
            quantidade = float(inteiro) + float(Fraction(frac))
        elif "/" in qtd_txt:
            quantidade = float(Fraction(qtd_txt))
        else:
            quantidade = float(qtd_txt)
    return {
        "nome": (nome or linha).strip(),
        "quantidade": quantidade,
        "unidade": unidade.lower() if unidade else None,
    }


def _parsear_rendimento(recipe_yield) -> int | None:
    if isinstance(recipe_yield, list):
        recipe_yield = recipe_yield[0] if recipe_yield else None
    if recipe_yield is None:
        return None
    m = re.search(r"\d+", str(recipe_yield))
    return int(m.group()) if m else None


def _buscar_recipe_jsonld(obj) -> dict | None:
    """Procura um @type Recipe em qualquer nível do JSON-LD (dict, lista,
    @graph, tipos combinados como ["Recipe", "NewsArticle"])."""
    if isinstance(obj, list):
        for item in obj:
            if encontrado := _buscar_recipe_jsonld(item):
                return encontrado
    elif isinstance(obj, dict):
        tipos = obj.get("@type", [])
        tipos = [tipos] if isinstance(tipos, str) else tipos
        if "Recipe" in tipos:
            return obj
        if graph := obj.get("@graph"):
            return _buscar_recipe_jsonld(graph)
    return None


def extrair_receita_de_html(html: str) -> dict:
    """Nível 2: parse determinístico do JSON-LD schema.org/Recipe."""
    for bloco in re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE,
    ):
        try:
            dados = json.loads(bloco.strip())
        except json.JSONDecodeError:
            continue
        recipe = _buscar_recipe_jsonld(dados)
        if recipe and recipe.get("recipeIngredient"):
            return {
                "titulo": recipe.get("name", "").strip(),
                "ingredientes": [
                    _parsear_linha_ingrediente(l) for l in recipe["recipeIngredient"]
                ],
                "rendimento_porcoes": _parsear_rendimento(recipe.get("recipeYield")),
                "fonte": "json-ld",
            }
    raise SemJsonLd("Página sem schema.org/Recipe utilizável")


def extrair_receita(url: str) -> dict:
    """Busca a página e extrai. SemJsonLd propaga para o agente acionar
    o Luna (nível 3 da cascata), com a URL anexada à exceção."""
    try:
        return extrair_receita_de_html(_get(url))
    except SemJsonLd as exc:
        raise SemJsonLd(str(exc), url=url) from exc

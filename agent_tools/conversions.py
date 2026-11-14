"""Conversão de unidades para a unidade base (kg, L, un).

Cobre o que aparece em receitas brasileiras e as unidades compostas da
planilha ("balde 2kg", "un 500ml"). O que a tabela não cobrir vai para o
subagente Luna (ADR 0003) — para_unidade_base devolve None nesse caso.
"""

import re
import unicodedata

# Unidade base por grandeza: massa -> kg, volume -> L, contagem -> un.
_UNIDADES: dict[str, tuple[str, float]] = {
    # massa
    "kg": ("kg", 1.0),
    "quilo": ("kg", 1.0),
    "quilos": ("kg", 1.0),
    "g": ("kg", 0.001),
    "grama": ("kg", 0.001),
    "gramas": ("kg", 0.001),
    # volume
    "l": ("L", 1.0),
    "litro": ("L", 1.0),
    "litros": ("L", 1.0),
    "ml": ("L", 0.001),
    "xicara": ("L", 0.240),
    "xicaras": ("L", 0.240),
    "copo": ("L", 0.200),
    "copos": ("L", 0.200),
    "colher de sopa": ("L", 0.015),
    "colheres de sopa": ("L", 0.015),
    "colher de cha": ("L", 0.005),
    "colheres de cha": ("L", 0.005),
    "colher de cafe": ("L", 0.002),
    # contagem
    "un": ("un", 1.0),
    "unidade": ("un", 1.0),
    "unidades": ("un", 1.0),
    "dente": ("un", 1.0),
    "dentes": ("un", 1.0),
    "folha": ("un", 1.0),
    "folhas": ("un", 1.0),
    "pitada": ("un", 1.0),
    "pitadas": ("un", 1.0),
    "maco": ("un", 1.0),
    "macos": ("un", 1.0),
    "lata": ("un", 1.0),
    "latas": ("un", 1.0),
    "caixa": ("un", 1.0),
    "caixas": ("un", 1.0),
    "pacote": ("un", 1.0),
    "pacotes": ("un", 1.0),
}

# Embalagens compostas da planilha: "balde 2kg", "un 500ml", "un 400g"...
_EMBALAGEM_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kg|g|ml|l)\b", re.IGNORECASE)


def normalizar(texto: str) -> str:
    """Minúsculo, sem acento, espaços colapsados. Usado para nomes de
    ingredientes e unidades em todo o sistema."""
    texto = unicodedata.normalize("NFKD", texto.strip().lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto)


def para_unidade_base(quantidade: float, unidade: str) -> tuple[float, str] | None:
    """Converte para a unidade base.

    Retorna (quantidade_na_base, unidade_base) ou None se a tabela não
    cobre a unidade — o chamador então aciona o Luna (ADR 0003).
    """
    unidade_norm = normalizar(unidade)
    # "2 colheres de sopa" coladas na quantidade, abreviações comuns.
    unidade_norm = re.sub(r"\bcols?\.\b", "colher de sopa", unidade_norm)
    unidade_norm = re.sub(r"\bxic\.?\b", "xicara", unidade_norm)
    entrada = _UNIDADES.get(unidade_norm)
    if entrada is None:
        return None
    base, fator = entrada
    return quantidade * fator, base


def decompor_embalagem(unidade: str) -> tuple[str, float] | None:
    """Interpreta a unidade da planilha como embalagem de compra.

    "balde 2kg"  -> ("kg", 2.0)   — 1 balde contém 2 kg
    "un 500ml"   -> ("L", 0.5)    — 1 unidade contém 500 ml
    "un"         -> ("un", 1.0)
    "kg"         -> ("kg", 1.0)

    Retorna (unidade_base, quantidade_base_por_embalagem) ou None.
    """
    unidade_norm = normalizar(unidade)
    m = _EMBALAGEM_RE.search(unidade_norm)
    if m:
        qtd = float(m.group(1).replace(",", "."))
        convertido = para_unidade_base(qtd, m.group(2))
        if convertido is None:
            return None
        return convertido[1], convertido[0]
    if unidade_norm in _UNIDADES:
        base, fator = _UNIDADES[unidade_norm]
        return base, fator  # "g" -> 0,001 kg; "ml" -> 0,001 L; "un" -> 1 un
    return None

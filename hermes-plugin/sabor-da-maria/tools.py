"""Handlers das tools do Sabor da Maria.

Cada handler embrulha uma função do núcleo determinístico (agent_tools/) e
devolve SEMPRE uma string JSON — sucesso ou erro estruturado. Nunca levanta:
exceções de domínio viram {"erro": <tipo>, ...} para o modelo reagir em
linguagem simples na conversa (regra: o modelo propõe, o código calcula).
"""

import json
import os
import sys
from pathlib import Path

# O plugin roda no processo do gateway (cwd ~/.hermes); o núcleo mora no repo.
_REPO = Path(os.environ.get(
    "SABOR_REPO", "/Users/kimgomes/Desktop/agent-challenge")).resolve()
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from agent_tools import basket, menu, pantry, pricing, recipes, state  # noqa: E402


def _ok(**payload) -> str:
    return json.dumps({"ok": True, **payload}, ensure_ascii=False, default=str)


def _erro(tipo: str, mensagem: str, **payload) -> str:
    return json.dumps({"ok": False, "erro": tipo, "mensagem": mensagem,
                       **payload}, ensure_ascii=False, default=str)


def _exe(fn, *args, **kwargs) -> str:
    """Roda fn devolvendo JSON; nunca levanta."""
    try:
        return fn(*args, **kwargs)
    except state.ViabilidadePendente as e:
        return _erro("viabilidade_pendente", str(e))
    except basket.OrcamentoEstourado as e:
        return _erro("orcamento_estourado", str(e))
    except basket.PratoNaoEncontrado as e:
        return _erro("prato_nao_encontrado", str(e))
    except pricing.SemPrecoCadastrado as e:
        return _erro("sem_preco_cadastrado", str(e))
    except pantry.ErroDeUnidade as e:
        return _erro("unidade_desconhecida", str(e))
    except recipes.SemJsonLd as e:
        return _erro("sem_json_ld",
                     "A página não tem receita estruturada. Use o texto bruto "
                     "desta URL e delegue a extração ao subagente.",
                     url=getattr(e, "url", None))
    except KeyError as e:
        return _erro("nao_encontrado", str(e))
    except ValueError as e:
        return _erro("valor_invalido", str(e))
    except Exception as e:  # última linha de defesa: o turn não pode quebrar
        return _erro(type(e).__name__, str(e))


# ---------------------------------------------------------------- fase

def get_phase(args: dict, **kwargs) -> str:
    return _exe(lambda: _ok(fase=state.get_phase()))


def set_phase(args: dict, **kwargs) -> str:
    fase = (args.get("fase") or "").strip()
    if not fase:
        return _erro("valor_invalido", "Informe a fase.")
    return _exe(lambda: (_ok(fase=fase) if state.set_phase(fase) is None else None))


# ---------------------------------------------------------------- despensa

def get_pantry(args: dict, **kwargs) -> str:
    return _exe(lambda: _ok(despensa=pantry.get_pantry()))


def tem_na_despensa(args: dict, **kwargs) -> str:
    def run():
        tem, disponivel = pantry.tem_na_despensa(
            args.get("ingrediente", ""), float(args.get("quantidade", 0)),
            args.get("unidade", ""))
        return _ok(tem=tem, disponivel_na_base=disponivel)
    return _exe(run)


def cadastrar_complemento(args: dict, **kwargs) -> str:
    def run():
        pantry.cadastrar_complemento(
            args.get("ingrediente", ""), float(args.get("qtd_embalagem", 0)),
            args.get("unidade", ""), float(args.get("preco_embalagem", 0)))
        return _ok()
    return _exe(run)


# ---------------------------------------------------------------- receitas

def buscar_receitas(args: dict, **kwargs) -> str:
    def run():
        ings = args.get("ingredientes") or []
        resultados = recipes.buscar_receitas(
            list(ings), int(args.get("max_resultados", 5)))
        return _ok(receitas=resultados)
    return _exe(run)


def extrair_receita(args: dict, **kwargs) -> str:
    url = (args.get("url") or "").strip()
    if not url:
        return _erro("valor_invalido", "Informe a URL da receita.")
    return _exe(lambda: _ok(receita=recipes.extrair_receita(url)))


def extrair_texto_bruto(args: dict, **kwargs) -> str:
    url = (args.get("url") or "").strip()
    if not url:
        return _erro("valor_invalido", "Informe a URL.")
    return _exe(lambda: _ok(
        texto=recipes.extrair_texto_bruto(url, int(args.get("max_chars", 12000)))))


# ---------------------------------------------------------------- pratos

def definir_prato(args: dict, **kwargs) -> str:
    def run():
        ings = [(i["nome"], float(i["quantidade"]), i["unidade"])
                for i in (args.get("ingredientes") or [])]
        basket.definir_prato(args.get("nome", ""),
                             int(args.get("rendimento_porcoes", 0)), ings)
        return _ok()
    return _exe(run)


def record_checklist_item(args: dict, **kwargs) -> str:
    def run():
        state.record_checklist_item(
            args.get("prato", ""), args.get("dimensao", ""),
            args.get("status", ""), args.get("detalhe", ""))
        return _ok()
    return _exe(run)


def checklist_completo(args: dict, **kwargs) -> str:
    def run():
        ok, pendentes = state.checklist_completo(args.get("prato", ""))
        return _ok(completo=ok, pendentes=pendentes)
    return _exe(run)


def accept_dish(args: dict, **kwargs) -> str:
    return _exe(lambda: _ok(reserva=state.accept_dish(args.get("prato", ""))))


# ---------------------------------------------------------------- preços

def cmv_por_porcao(args: dict, **kwargs) -> str:
    return _exe(lambda: _ok(cmv=pricing.cmv_por_porcao(args.get("prato", ""))))


def cenarios_de_preco(args: dict, **kwargs) -> str:
    def run():
        cmv = pricing.cmv_por_porcao(args.get("prato", ""))
        return _ok(cmv=cmv, preco_minimo=pricing.preco_minimo(cmv["cmv_porcao"]),
                   cenarios=pricing.cenarios_de_preco(cmv["cmv_porcao"]))
    return _exe(run)


def registrar_preco_escolhido(args: dict, **kwargs) -> str:
    def run():
        basket.registrar_preco_escolhido(args.get("prato", ""),
                                         float(args.get("preco", 0)))
        return _ok()
    return _exe(run)


def cesta_atual(args: dict, **kwargs) -> str:
    return _exe(lambda: _ok(cesta=basket.cesta_atual()))


# ---------------------------------------------------------------- cardápio

def gerar_cardapio(args: dict, **kwargs) -> str:
    def run():
        saida = menu.gerar_cardapio()
        return _ok(caminho=str((_REPO / saida).resolve()))
    return _exe(run)


def gerar_pdf(args: dict, **kwargs) -> str:
    def run():
        saida = menu.gerar_pdf()
        return _ok(caminho=str((_REPO / saida).resolve()))
    return _exe(run)

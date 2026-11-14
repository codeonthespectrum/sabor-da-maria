"""Estado do fluxo de consultoria e gate de viabilidade (ADR 0002).

Fases: briefing -> descoberta -> viabilidade -> precificacao -> cardapio.
A conversa pode retroceder; o agente nunca perde a fase de vista.

Regra de negócio que vive AQUI (nunca no prompt): accept_dish só aceita
um prato cujo checklist de viabilidade está completo e sem impedimentos.
Enquanto houver pendência, recusa devolvendo o que falta perguntar —
é isso que força o agente a elicitar em vez de assumir.
"""

from . import basket
from .conversions import normalizar
from .db import get_conn

FASES = ["briefing", "descoberta", "viabilidade", "precificacao", "cardapio"]

DIMENSOES = ("utensilios", "tecnicas", "restricoes_operacionais")


class ViabilidadePendente(RuntimeError):
    """Checklist incompleto ou com impedimento: o aceite é recusado e o
    erro lista o que falta perguntar à Dona Maria."""


def get_phase() -> str:
    """Retorna a fase atual da consultoria."""
    conn = get_conn()
    row = conn.execute("SELECT fase FROM consultoria WHERE id = 1").fetchone()
    conn.close()
    return row["fase"]


def set_phase(fase: str) -> None:
    """Avança ou retrocede a fase. Valida contra FASES."""
    fase_norm = normalizar(fase)
    if fase_norm not in FASES:
        raise ValueError(f"Fase inválida: {fase!r}. Válidas: {', '.join(FASES)}")
    conn = get_conn()
    with conn:
        conn.execute("UPDATE consultoria SET fase = ? WHERE id = 1", (fase_norm,))
    conn.close()


def get_checklist(prato: str) -> dict:
    """Checklist de viabilidade do prato:
    {dimensao: {status: 'pendente'|'ok'|'impedimento', detalhe: str}}.
    Dimensões nunca registradas aparecem como pendentes."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT dimensao, status, detalhe FROM checklist_viabilidade WHERE prato = ?",
        (normalizar(prato),),
    ).fetchall()
    conn.close()
    registrado = {r["dimensao"]: {"status": r["status"], "detalhe": r["detalhe"]}
                  for r in rows}
    return {d: registrado.get(d, {"status": "pendente", "detalhe": ""})
            for d in DIMENSOES}


def record_checklist_item(prato: str, dimensao: str, status: str, detalhe: str) -> None:
    """Registra a resposta da Dona Maria para uma dimensão do checklist."""
    dimensao_norm = normalizar(dimensao).replace(" ", "_")
    status_norm = normalizar(status)
    if dimensao_norm not in DIMENSOES:
        raise ValueError(f"Dimensão inválida: {dimensao!r}. Válidas: {', '.join(DIMENSOES)}")
    if status_norm not in ("pendente", "ok", "impedimento"):
        raise ValueError(f"Status inválido: {status!r}. Válidos: pendente, ok, impedimento")
    conn = get_conn()
    with conn:
        conn.execute(
            "INSERT INTO checklist_viabilidade (prato, dimensao, status, detalhe)"
            " VALUES (?, ?, ?, ?)"
            " ON CONFLICT(prato, dimensao) DO UPDATE SET"
            " status = excluded.status, detalhe = excluded.detalhe",
            (normalizar(prato), dimensao_norm, status_norm, detalhe.strip()),
        )
    conn.close()


def checklist_completo(prato: str) -> tuple[bool, list[str]]:
    """(True, []) se completo e sem impedimentos; (False, [pendências]).
    Usado pelo gate do accept_dish."""
    checklist = get_checklist(prato)
    pendentes = []
    for dimensao, item in checklist.items():
        if item["status"] == "pendente":
            pendentes.append(f"{dimensao} (não perguntado)")
        elif item["status"] == "impedimento":
            pendentes.append(f"{dimensao} (impedimento: {item['detalhe']})")
    return (not pendentes, pendentes)


def accept_dish(prato: str) -> dict:
    """Aceita um prato: valida o checklist (gate) e reserva o orçamento.

    Levanta ViabilidadePendente listando o que falta perguntar, ou
    basket.OrcamentoEstourado se a cesta não couber nos R$ 80."""
    ok, pendentes = checklist_completo(prato)
    if not ok:
        raise ViabilidadePendente(
            f"Não posso aceitar '{prato}' ainda. Falta confirmar: "
            + "; ".join(pendentes)
        )
    return basket.reservar(prato)

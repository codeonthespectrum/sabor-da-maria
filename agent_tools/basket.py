"""Cesta de compras deduplicada e reserva de orçamento (ADR 0001).

ORÇAMENTO MEDE COMPRA: o valor reservado é o preço CHEIO da(s) embalagem(ns),
nunca a fração usada na receita (isso é CMV — pricing.py).

Semântica decidida na sessão de design:
- Reserva acontece na ACEITAÇÃO do prato (reservar).
- A cesta é deduplicada e GLOBAL: mesmo complemento em dois pratos soma
  quantidades; a despensa também é compartilhada entre os pratos aceitos.
  A quantidade total faltante determina quantas embalagens comprar.
- Desistir de um prato (liberar) recalcula a cesta e devolve o que só
  aquele prato consumia do orçamento.
- Orçamento inicial: R$ 80,00.
"""

import math

from .conversions import normalizar, para_unidade_base
from .db import get_conn

ORCAMENTO_INICIAL = 80.00
_EPS = 1e-9


class OrcamentoEstourado(RuntimeError):
    """A cesta dos pratos aceitos custa mais que o orçamento restante."""


class PratoNaoEncontrado(KeyError):
    pass


def definir_prato(nome: str, rendimento_porcoes: int,
                  ingredientes: list[tuple[str, float, str]]) -> None:
    """Registra/atualiza um prato candidato e sua receita.

    ingredientes: [(nome, quantidade, unidade)] — convertidos para a
    unidade base na entrada. O rendimento pode ser corrigido depois com
    uma nova chamada."""
    conn = get_conn()
    chave = normalizar(nome)
    with conn:
        conn.execute(
            "INSERT INTO pratos (nome, nome_exibicao, rendimento_porcoes)"
            " VALUES (?, ?, ?)"
            " ON CONFLICT(nome) DO UPDATE SET rendimento_porcoes = excluded.rendimento_porcoes",
            (chave, nome.strip(), int(rendimento_porcoes)),
        )
        conn.execute("DELETE FROM prato_ingredientes WHERE prato = ?", (chave,))
        for ing, qtd, unidade in ingredientes:
            convertido = para_unidade_base(qtd, unidade)
            if convertido is None:
                raise ValueError(f"Unidade não reconhecida: {unidade!r} ({ing})")
            qtd_base, unidade_base = convertido
            conn.execute(
                "INSERT INTO prato_ingredientes VALUES (?, ?, ?, ?)",
                (chave, normalizar(ing), qtd_base, unidade_base),
            )
    conn.close()


def _prato(conn, nome: str):
    row = conn.execute("SELECT * FROM pratos WHERE nome = ?", (normalizar(nome),)).fetchone()
    if row is None:
        raise PratoNaoEncontrado(nome)
    return row


def _necessidade_aceitos(conn) -> dict[str, tuple[float, str]]:
    """Soma dos ingredientes de TODOS os pratos aceitos, por ingrediente."""
    rows = conn.execute(
        "SELECT pi.ingrediente, pi.unidade_base, SUM(pi.quantidade_base) AS total"
        " FROM prato_ingredientes pi JOIN pratos p ON p.nome = pi.prato"
        " WHERE p.status = 'aceito' GROUP BY pi.ingrediente, pi.unidade_base"
    ).fetchall()
    return {r["ingrediente"]: (r["total"], r["unidade_base"]) for r in rows}


def _calcular_cesta(conn) -> dict:
    """Cesta global deduplicada: necessidade dos aceitos menos a despensa,
    arredondada para cima em embalagens inteiras. ORÇAMENTO MEDE COMPRA."""
    necessidade = _necessidade_aceitos(conn)
    itens, sem_preco = [], []
    for ingrediente, (qtd_total, unidade_base) in sorted(necessidade.items()):
        desp = conn.execute(
            "SELECT quantidade_base FROM despensa WHERE ingrediente = ?", (ingrediente,)
        ).fetchone()
        em_casa = desp["quantidade_base"] if desp else 0.0
        faltante = max(0.0, qtd_total - em_casa)
        if faltante <= _EPS:
            continue
        preco = conn.execute(
            "SELECT nome_exibicao, embalagem_qtd_base, preco_embalagem"
            " FROM precos WHERE ingrediente = ?", (ingrediente,)
        ).fetchone()
        if preco is None:
            sem_preco.append(ingrediente)
            continue
        embalagens = math.ceil(faltante / preco["embalagem_qtd_base"] - _EPS)
        itens.append({
            "ingrediente": preco["nome_exibicao"],
            "faltante_base": round(faltante, 4),
            "unidade_base": unidade_base,
            "embalagens": embalagens,
            "preco_embalagem": preco["preco_embalagem"],
            "custo": round(embalagens * preco["preco_embalagem"], 2),
        })
    total = round(sum(i["custo"] for i in itens), 2)
    return {
        "itens": itens,
        "sem_preco": sem_preco,
        "reservado_total": total,
        "orcamento_restante": round(ORCAMENTO_INICIAL - total, 2),
    }


def complementos_do_prato(prato: str) -> list[dict]:
    """O que falta na despensa para UM prato, isoladamente (visão didática
    para a conversa; a reserva de verdade é global — ver cesta_atual)."""
    conn = get_conn()
    _prato(conn, prato)
    rows = conn.execute(
        "SELECT ingrediente, quantidade_base, unidade_base"
        " FROM prato_ingredientes WHERE prato = ?", (normalizar(prato),)
    ).fetchall()
    faltantes = []
    for r in rows:
        desp = conn.execute(
            "SELECT quantidade_base FROM despensa WHERE ingrediente = ?", (r["ingrediente"],)
        ).fetchone()
        em_casa = desp["quantidade_base"] if desp else 0.0
        faltante = r["quantidade_base"] - em_casa
        if faltante > _EPS:
            preco = conn.execute(
                "SELECT preco_embalagem / embalagem_qtd_base AS pu FROM precos WHERE ingrediente = ?",
                (r["ingrediente"],),
            ).fetchone()
            faltantes.append({
                "ingrediente": r["ingrediente"],
                "quantidade_faltante": round(faltante, 4),
                "unidade_base": r["unidade_base"],
                "preco_unitario": preco["pu"] if preco else None,
            })
    conn.close()
    return faltantes


def reservar(prato: str) -> dict:
    """Chamado na aceitação. Marca o prato como aceito e recalcula a cesta.

    Levanta OrcamentoEstourado (sem aceitar o prato) se a cesta não couber
    no orçamento — o agente então propõe substituição ou descarte (Q16).
    Falha também se algum faltante não tem preço cadastrado: o agente
    precisa cadastrar o complemento antes (pantry.cadastrar_complemento).
    """
    conn = get_conn()
    row = _prato(conn, prato)
    if row["status"] == "aceito":
        cesta = _calcular_cesta(conn)
        conn.close()
        return cesta

    conn.execute("UPDATE pratos SET status = 'aceito' WHERE nome = ?", (row["nome"],))
    cesta = _calcular_cesta(conn)
    if cesta["sem_preco"]:
        conn.close()
        raise ValueError(
            f"Sem preço cadastrado para: {', '.join(cesta['sem_preco'])}. "
            "Cadastre com pantry.cadastrar_complemento antes de aceitar."
        )
    if cesta["reservado_total"] > ORCAMENTO_INICIAL + _EPS:
        conn.execute("UPDATE pratos SET status = 'candidato' WHERE nome = ?", (row["nome"],))
        conn.commit()
        conn.close()
        raise OrcamentoEstourado(
            f"Cesta de R$ {cesta['reservado_total']:.2f} estoura o orçamento de "
            f"R$ {ORCAMENTO_INICIAL:.2f}. Falta cobrir R$ "
            f"{-cesta['orcamento_restante']:.2f}."
        )
    conn.commit()
    conn.close()
    return cesta


def liberar(prato: str) -> dict:
    """Desistência: o prato volta a candidato, a cesta é recalculada e a
    reserva correspondente é liberada (itens compartilhados permanecem)."""
    conn = get_conn()
    row = _prato(conn, prato)
    with conn:
        conn.execute(
            "UPDATE pratos SET status = 'candidato', preco_escolhido = NULL WHERE nome = ?",
            (row["nome"],),
        )
    cesta = _calcular_cesta(conn)
    conn.close()
    return cesta


def registrar_preco_escolhido(prato: str, preco: float) -> None:
    """Registra o preço por porção que a Dona Maria escolheu entre os
    cenários. A decisão é sempre dela — o agente apresenta, ela escolhe."""
    conn = get_conn()
    row = _prato(conn, prato)
    with conn:
        conn.execute(
            "UPDATE pratos SET preco_escolhido = ? WHERE nome = ?",
            (float(preco), row["nome"]),
        )
    conn.close()


def cesta_atual() -> dict:
    """Estado consolidado: itens, quantidades, embalagens necessárias,
    reservado_total e orcamento_restante."""
    conn = get_conn()
    cesta = _calcular_cesta(conn)
    conn.close()
    return cesta

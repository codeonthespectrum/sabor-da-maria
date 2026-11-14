"""CMV por porção e cenários de preço — 100% determinístico (ADR 0001 e 0003).

CMV MEDE CONSUMO: quantidade usada x custo unitário, somado sobre todos os
ingredientes (despensa + complementos). Nunca o preço cheio da embalagem.

Taxa da plataforma: 10% sobre a venda. Preço P -> Dona Maria recebe 0,90·P.
Preço mínimo = CMV / 0,90. Lucro = 0,90·P - CMV.
"""

import math

from .conversions import normalizar
from .db import get_conn

TAXA_PLATAFORMA = 0.10

# Margens-alvo sobre o preço de venda (lucro / P) para os 3 cenários.
_MARGENS = [("Econômico", 0.40), ("Equilibrado", 0.50), ("Premium", 0.60)]


class SemPrecoCadastrado(RuntimeError):
    """Ingrediente da receita sem preço conhecido — CMV não fecha."""


def cmv_por_porcao(prato: str, rendimento_porcoes: int | None = None) -> dict:
    """{cmv_receita, cmv_porcao, itens: [{ingrediente, qtd, unidade,
    custo_unitario, custo_parcial, origem: despensa|complemento}]}.

    Falha com a lista do que falta se algum ingrediente não tem preço
    conhecido — o agente precisa cadastrar o complemento antes."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM pratos WHERE nome = ?", (normalizar(prato),)).fetchone()
    if row is None:
        conn.close()
        raise KeyError(f"Prato não registrado: {prato}")
    rendimento = int(rendimento_porcoes or row["rendimento_porcoes"])

    itens, sem_preco = [], []
    for r in conn.execute(
        "SELECT ingrediente, quantidade_base, unidade_base FROM prato_ingredientes WHERE prato = ?",
        (row["nome"],),
    ).fetchall():
        preco = conn.execute(
            "SELECT nome_exibicao, preco_embalagem / embalagem_qtd_base AS pu, origem"
            " FROM precos WHERE ingrediente = ?", (r["ingrediente"],)
        ).fetchone()
        desp = conn.execute(
            "SELECT 1 FROM despensa WHERE ingrediente = ?", (r["ingrediente"],)
        ).fetchone()
        if preco is None:
            sem_preco.append(r["ingrediente"])
            continue
        custo_parcial = round(r["quantidade_base"] * preco["pu"], 4)
        itens.append({
            "ingrediente": preco["nome_exibicao"],
            "qtd": round(r["quantidade_base"], 4),
            "unidade": r["unidade_base"],
            "custo_unitario": round(preco["pu"], 4),
            "custo_parcial": custo_parcial,
            # origem do CONSUMO: veio do estoque ou da cesta de compras
            "origem": "despensa" if desp else "complemento",
        })
    conn.close()
    if sem_preco:
        raise SemPrecoCadastrado(
            f"Sem preço para: {', '.join(sem_preco)}. "
            "Cadastre com pantry.cadastrar_complemento."
        )
    cmv_receita = round(sum(i["custo_parcial"] for i in itens), 2)
    return {
        "cmv_receita": cmv_receita,
        "rendimento_porcoes": rendimento,
        "cmv_porcao": round(cmv_receita / rendimento, 2),
        "itens": itens,
    }


def preco_minimo(cmv: float) -> float:
    """Menor preço sem prejuízo: CMV / (1 - taxa). Aceita o CMV por porção
    ou o dict completo de cmv_por_porcao."""
    if isinstance(cmv, dict):
        cmv = cmv["cmv_porcao"]
    return round(cmv / (1 - TAXA_PLATAFORMA), 2)


def _arredondar_pra_cima(valor: float, passo: float = 0.50) -> float:
    """Preços amigáveis de cardápio: sempre múltiplos de R$ 0,50, para cima
    (arredondar para baixo pode furar o preço mínimo)."""
    return round(math.ceil(valor / passo - 1e-9) * passo, 2)


def cenarios_de_preco(cmv: float) -> list[dict]:
    """3 cenários de margem, cada um com a matemática visível:
    {nome, preco, repasse: 0.9*P, lucro, margem_sobre_preco}.

    A decisão final é sempre da Dona Maria — o agente apresenta, ela escolhe."""
    if isinstance(cmv, dict):
        cmv = cmv["cmv_porcao"]
    minimo = preco_minimo(cmv)
    cenarios = []
    for nome, margem_alvo in _MARGENS:
        # lucro = 0,9·P - CMV = margem·P  =>  P = CMV / (0,9 - margem)
        bruto = cmv / (1 - TAXA_PLATAFORMA - margem_alvo)
        preco = max(_arredondar_pra_cima(bruto), _arredondar_pra_cima(minimo))
        repasse = round(preco * (1 - TAXA_PLATAFORMA), 2)
        lucro = round(repasse - cmv, 2)
        cenarios.append({
            "nome": nome,
            "preco": preco,
            "repasse": repasse,
            "lucro": lucro,
            "margem_sobre_preco": round(lucro / preco, 4),
        })
    return cenarios

"""Geração do cardápio de lançamento (artefato final, Markdown).

Cada prato aceito: ingredientes, CMV por porção, cenários de preço e o
preço escolhido pela Dona Maria. Ao final: cesta de compras consolidada,
total reservado e orçamento restante.
"""

from pathlib import Path

from . import basket, pricing
from .db import get_conn


def _fmt(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def gerar_cardapio(path_saida: str = "cardapio_lancamento.md") -> str:
    """Gera o Markdown do cardápio a partir dos pratos aceitos.
    Retorna o caminho do arquivo gerado."""
    conn = get_conn()
    pratos = conn.execute(
        "SELECT nome_exibicao, rendimento_porcoes, preco_escolhido"
        " FROM pratos WHERE status = 'aceito' ORDER BY nome_exibicao"
    ).fetchall()
    conn.close()

    linhas = ["# Sabor da Maria — Cardápio de Lançamento", ""]
    for p in pratos:
        cmv = pricing.cmv_por_porcao(p["nome_exibicao"])
        linhas += [f"## {p['nome_exibicao']}", ""]
        linhas.append("| Ingrediente | Quantidade | Custo parcial | Origem |")
        linhas.append("|---|---|---|---|")
        for item in cmv["itens"]:
            linhas.append(
                f"| {item['ingrediente']} | {item['qtd']:g} {item['unidade']} "
                f"| {_fmt(item['custo_parcial'])} | {item['origem']} |"
            )
        linhas += [
            "",
            f"- **CMV da receita:** {_fmt(cmv['cmv_receita'])} "
            f"(rende {cmv['rendimento_porcoes']} porções)",
            f"- **CMV por porção:** {_fmt(cmv['cmv_porcao'])}",
            f"- **Preço mínimo (sem prejuízo):** {_fmt(pricing.preco_minimo(cmv))}",
            "",
            "| Cenário | Preço | Dona Maria recebe | Lucro por porção |",
            "|---|---|---|---|",
        ]
        for c in pricing.cenarios_de_preco(cmv):
            linhas.append(
                f"| {c['nome']} | {_fmt(c['preco'])} | {_fmt(c['repasse'])} "
                f"| {_fmt(c['lucro'])} |"
            )
        escolhido = _fmt(p["preco_escolhido"]) if p["preco_escolhido"] else "_a decidir_"
        linhas += ["", f"**Preço escolhido pela Dona Maria: {escolhido}**", ""]

    cesta = basket.cesta_atual()
    linhas += ["---", "", "## Cesta de compras (complementos)", ""]
    if cesta["itens"]:
        linhas.append("| Item | Falta | Embalagens | Custo |")
        linhas.append("|---|---|---|---|")
        for i in cesta["itens"]:
            linhas.append(
                f"| {i['ingrediente']} | {i['faltante_base']:g} {i['unidade_base']} "
                f"| {i['embalagens']} | {_fmt(i['custo'])} |"
            )
    else:
        linhas.append("Nenhum complemento necessário — a despensa cobre tudo.")
    linhas += [
        "",
        f"- **Total reservado:** {_fmt(cesta['reservado_total'])}",
        f"- **Orçamento restante:** {_fmt(cesta['orcamento_restante'])} "
        f"(de {_fmt(basket.ORCAMENTO_INICIAL)})",
        "",
    ]

    Path(path_saida).write_text("\n".join(linhas), encoding="utf-8")
    return path_saida

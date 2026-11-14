"""Geração do cardápio de lançamento (artefato final, Markdown).

Cada prato aceito: ingredientes, CMV por porção, cenários de preço e o
preço escolhido pela Dona Maria. Ao final: cesta de compras consolidada,
total reservado e orçamento restante.
"""

from pathlib import Path

from . import basket, pricing
from .conversions import nome_bonito
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
        linhas += [f"## {nome_bonito(p['nome_exibicao'])}", ""]
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


def gerar_pdf(path_saida: str = "cardapio_lancamento.pdf") -> str:
    """Gera o cardápio final em PDF — o artefato entregue à Dona Maria.

    Linguagem simples, sem jargão: nada de "CMV" impresso. Os números são
    os mesmos do Markdown (fonte única: pricing/basket)."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer,
                                    Table, TableStyle)

    estilos = getSampleStyleSheet()
    titulo = estilos["Title"]
    h2 = estilos["Heading2"]
    corpo = estilos["BodyText"]

    doc = SimpleDocTemplate(path_saida, pagesize=A4,
                            leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=20 * mm, bottomMargin=20 * mm,
                            title="Sabor da Maria — Cardápio de Lançamento")
    story = [Paragraph("Sabor da Maria — Cardápio de Lançamento", titulo),
             Spacer(1, 6 * mm)]

    estilo_tab = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2e3d5")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWPADDING", (0, 0), (-1, -1), 4),
        ("COLPADDING", (0, 0), (-1, -1), 6),
    ])

    conn = get_conn()
    pratos = conn.execute(
        "SELECT nome_exibicao, rendimento_porcoes, preco_escolhido"
        " FROM pratos WHERE status = 'aceito' ORDER BY nome_exibicao"
    ).fetchall()
    conn.close()

    for p in pratos:
        cmv = pricing.cmv_por_porcao(p["nome_exibicao"])
        story.append(Paragraph(nome_bonito(p["nome_exibicao"]), h2))
        story.append(Spacer(1, 2 * mm))

        tab = Table([["Ingrediente", "Quantidade", "Custo parcial", "Origem"]]
                    + [[i["ingrediente"], f"{i['qtd']:g} {i['unidade']}",
                        _fmt(i["custo_parcial"]), i["origem"]]
                       for i in cmv["itens"]])
        tab.setStyle(estilo_tab)
        story.append(tab)
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            f"Custo da receita: <b>{_fmt(cmv['cmv_receita'])}</b> "
            f"(rende {cmv['rendimento_porcoes']} marmitas) — "
            f"custo por marmita: <b>{_fmt(cmv['cmv_porcao'])}</b>. "
            f"Preço mínimo para não ter prejuízo: "
            f"<b>{_fmt(pricing.preco_minimo(cmv))}</b>.", corpo))
        story.append(Spacer(1, 2 * mm))

        cen = Table([["Opção de preço", "Preço", "Você recebe", "Lucro por marmita"]]
                    + [[c["nome"], _fmt(c["preco"]), _fmt(c["repasse"]),
                        _fmt(c["lucro"])]
                       for c in pricing.cenarios_de_preco(cmv)])
        cen.setStyle(estilo_tab)
        story.append(cen)
        story.append(Spacer(1, 2 * mm))
        escolhido = (_fmt(p["preco_escolhido"]) if p["preco_escolhido"]
                     else "a decidir")
        story.append(Paragraph(
            f"<b>Preço escolhido: {escolhido}</b>", corpo))
        story.append(Spacer(1, 6 * mm))

    cesta = basket.cesta_atual()
    story.append(Paragraph("Lista de compras (o que falta na despensa)", h2))
    story.append(Spacer(1, 2 * mm))
    if cesta["itens"]:
        tab = Table([["Item", "Falta", "Embalagens", "Custo"]]
                    + [[i["ingrediente"], f"{i['faltante_base']:g} {i['unidade_base']}",
                        str(i["embalagens"]), _fmt(i["custo"])]
                       for i in cesta["itens"]])
        tab.setStyle(estilo_tab)
        story.append(tab)
    else:
        story.append(Paragraph(
            "Nada a comprar — a despensa cobre tudo.", corpo))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        f"Total a gastar: <b>{_fmt(cesta['reservado_total'])}</b> — "
        f"sobra do orçamento: <b>{_fmt(cesta['orcamento_restante'])}</b> "
        f"(de {_fmt(basket.ORCAMENTO_INICIAL)}).", corpo))

    doc.build(story)
    return path_saida

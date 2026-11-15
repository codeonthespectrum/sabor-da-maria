"""Despensa: ingestão do xlsx, consulta de estoque e preço unitário.

O xlsx tem duas abas:
- Despensa: Ingrediente, Quantidade em estoque, Unidade
- Precos:   Ingrediente, Quantidade comprada, Unidade, Preço total pago

Preço unitário = preço total pago / quantidade comprada (cruzamento das abas).
Unidades compostas ("balde 2kg", "un 500ml") são normalizadas para a
unidade base (kg, L, un) na ingestão — ver conversions.py.
"""

from .conversions import decompor_embalagem, normalizar, para_unidade_base
from .db import get_conn


class ErroDeUnidade(ValueError):
    """Unidade fora da tabela de conversões — acionar o Luna (ADR 0003)."""


def _ler_aba(path: str, nome_aba: str) -> list[tuple]:
    # openpyxl é importado aqui (e não no topo) para o plugin Hermes carregar
    # sem a dependência — o gateway só lê a despensa, quem ingere xlsx é o
    # setup local com a venv do projeto.
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True)
    if nome_aba not in wb.sheetnames:
        raise ValueError(f"Aba '{nome_aba}' não encontrada. Abas: {wb.sheetnames}")
    linhas = [row for row in wb[nome_aba].iter_rows(values_only=True)]
    wb.close()
    return [l for l in linhas[1:] if l and l[0]]  # descarta cabeçalho e vazias


def ingest_xlsx(path: str) -> dict:
    """Carrega a planilha para o banco. Retorna resumo para o agente
    confirmar com a Dona Maria ('recebi sua despensa: 37 itens...')."""
    despensa = _ler_aba(path, "Despensa")
    precos = _ler_aba(path, "Precos")

    conn = get_conn()
    n_itens, sem_preco = 0, []
    with conn:
        conn.execute("DELETE FROM despensa")
        conn.execute("DELETE FROM precos WHERE origem = 'planilha'")

        for nome, qtd, unidade in despensa:
            emb = decompor_embalagem(str(unidade))
            if emb is None:
                raise ErroDeUnidade(f"Unidade não reconhecida na aba Despensa: {unidade!r} ({nome})")
            unidade_base, por_embalagem = emb
            conn.execute(
                "INSERT OR REPLACE INTO despensa VALUES (?, ?, ?, ?)",
                (normalizar(str(nome)), str(nome).strip(), float(qtd) * por_embalagem, unidade_base),
            )
            n_itens += 1

        for nome, qtd, unidade, preco in precos:
            emb = decompor_embalagem(str(unidade))
            if emb is None:
                raise ErroDeUnidade(f"Unidade fora da tabela na aba Precos: {unidade!r} ({nome})")
            unidade_base, por_embalagem = emb
            conn.execute(
                "INSERT OR REPLACE INTO precos VALUES (?, ?, ?, ?, ?, 'planilha')",
                (normalizar(str(nome)), str(nome).strip(), float(qtd) * por_embalagem,
                 unidade_base, float(preco)),
            )

    # Cruzamento: quem tem estoque sem preço conhecido (não dá para calcular CMV).
    for row in conn.execute(
        "SELECT d.nome_exibicao FROM despensa d LEFT JOIN precos p"
        " ON d.ingrediente = p.ingrediente WHERE p.ingrediente IS NULL"
    ):
        sem_preco.append(row["nome_exibicao"])
    conn.close()
    return {"itens": n_itens, "sem_preco": sem_preco}


def get_pantry() -> list[dict]:
    """Estoque atual: [{ingrediente, quantidade, unidade_base, preco_unitario}]."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT d.nome_exibicao AS ingrediente, d.quantidade_base AS quantidade,"
        " d.unidade_base, p.preco_embalagem / p.embalagem_qtd_base AS preco_unitario"
        " FROM despensa d LEFT JOIN precos p ON d.ingrediente = p.ingrediente"
        " ORDER BY d.nome_exibicao"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def preco_unitario(ingrediente: str) -> float | None:
    """Preço por unidade base (R$/kg, R$/L, R$/un). None se não consta."""
    conn = get_conn()
    row = conn.execute(
        "SELECT preco_embalagem / embalagem_qtd_base AS pu FROM precos WHERE ingrediente = ?",
        (normalizar(ingrediente),),
    ).fetchone()
    conn.close()
    return row["pu"] if row else None


def tem_na_despensa(ingrediente: str, quantidade: float, unidade: str) -> tuple[bool, float]:
    """(tem_suficiente, quantidade_disponivel_na_unidade_base).

    Converte a quantidade pedida para a unidade base antes de comparar."""
    pedido = para_unidade_base(quantidade, unidade)
    if pedido is None:
        raise ErroDeUnidade(f"Unidade não reconhecida: {unidade!r}")
    qtd_base, unidade_base = pedido

    conn = get_conn()
    row = conn.execute(
        "SELECT quantidade_base, unidade_base FROM despensa WHERE ingrediente = ?",
        (normalizar(ingrediente),),
    ).fetchone()
    conn.close()
    if row is None:
        return False, 0.0
    if row["unidade_base"] != unidade_base:
        raise ErroDeUnidade(
            f"Unidade incompatível para {ingrediente}: receita em {unidade_base},"
            f" despensa em {row['unidade_base']}"
        )
    return row["quantidade_base"] >= qtd_base, row["quantidade_base"]


def cadastrar_complemento(ingrediente: str, qtd_embalagem: float, unidade: str,
                          preco_embalagem: float) -> None:
    """Registra o preço de um complemento que não está na planilha
    (ex.: creme de leite). O agente descobre o preço na conversa ou na busca
    e cadastra aqui — sem preço, a cesta não fecha (ver basket.py)."""
    emb = decompor_embalagem(unidade)
    if emb is None:
        raise ErroDeUnidade(f"Unidade não reconhecida: {unidade!r}")
    unidade_base, por_embalagem = emb
    conn = get_conn()
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO precos VALUES (?, ?, ?, ?, ?, 'complemento')",
            (normalizar(ingrediente), ingrediente.strip(),
             float(qtd_embalagem) * por_embalagem, unidade_base, float(preco_embalagem)),
        )
    conn.close()

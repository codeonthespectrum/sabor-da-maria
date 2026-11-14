"""Banco de dados SQLite — fonte da verdade do estado de negócio.

Nada aqui é memória de conversa: é dado transacional (ver CONTEXT.md e ADR 0001).
O caminho do banco é configurável para testes (set_db_path / env SABOR_DB).
"""

import os
import sqlite3
from pathlib import Path

_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "sabor.db"
_db_path: Path | None = None


def set_db_path(path: str | os.PathLike) -> None:
    """Aponta o módulo para outro banco (usado pelos testes)."""
    global _db_path
    _db_path = Path(path)


def reset_db_path() -> None:
    """Volta ao banco padrão (tearDown dos testes)."""
    global _db_path
    _db_path = None


def get_db_path() -> Path:
    if _db_path is not None:
        return _db_path
    env = os.environ.get("SABOR_DB")
    return Path(env) if env else _DEFAULT_PATH


def get_conn() -> sqlite3.Connection:
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_schema(conn)
    return conn


SCHEMA = """
-- O que ela tem hoje (aba Despensa, normalizada para a unidade base).
CREATE TABLE IF NOT EXISTS despensa (
    ingrediente      TEXT PRIMARY KEY,   -- nome normalizado (minúsculo, sem acento)
    nome_exibicao    TEXT NOT NULL,      -- nome como veio na planilha
    quantidade_base  REAL NOT NULL,      -- na unidade base (kg, L, un)
    unidade_base     TEXT NOT NULL
);

-- Quanto ela pagou (aba Precos) + complementos cadastrados depois.
-- A embalagem é a unidade de COMPRA: quantidade_base por embalagem, preco_total por embalagem.
CREATE TABLE IF NOT EXISTS precos (
    ingrediente           TEXT PRIMARY KEY,
    nome_exibicao         TEXT NOT NULL,
    embalagem_qtd_base    REAL NOT NULL, -- ex.: 0.5 (kg) para "un 500g"
    unidade_base          TEXT NOT NULL,
    preco_embalagem       REAL NOT NULL, -- R$ por embalagem
    origem                TEXT NOT NULL DEFAULT 'planilha'  -- 'planilha' | 'complemento'
);

-- Pratos conhecidos pelo agente e seu ciclo de vida.
CREATE TABLE IF NOT EXISTS pratos (
    nome                TEXT PRIMARY KEY,
    nome_exibicao       TEXT NOT NULL,
    rendimento_porcoes  INTEGER NOT NULL,
    status              TEXT NOT NULL DEFAULT 'candidato'
                        CHECK (status IN ('candidato', 'aceito', 'descartado')),
    preco_escolhido     REAL,
    motivo_descarte     TEXT
);

-- Ingredientes da receita de cada prato, já na unidade base.
CREATE TABLE IF NOT EXISTS prato_ingredientes (
    prato           TEXT NOT NULL REFERENCES pratos(nome) ON DELETE CASCADE,
    ingrediente     TEXT NOT NULL,
    quantidade_base REAL NOT NULL,
    unidade_base    TEXT NOT NULL,
    PRIMARY KEY (prato, ingrediente)
);

-- Fase atual do fluxo de consultoria (uma linha só).
CREATE TABLE IF NOT EXISTS consultoria (
    id    INTEGER PRIMARY KEY CHECK (id = 1),
    fase  TEXT NOT NULL DEFAULT 'briefing'
);
INSERT OR IGNORE INTO consultoria (id, fase) VALUES (1, 'briefing');

-- Checklist de viabilidade por prato (ADR 0002): cada dimensão começa
-- pendente e só a resposta da Dona Maria a move.
CREATE TABLE IF NOT EXISTS checklist_viabilidade (
    prato     TEXT NOT NULL,
    dimensao  TEXT NOT NULL CHECK (dimensao IN ('utensilios', 'tecnicas', 'restricoes_operacionais')),
    status    TEXT NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente', 'ok', 'impedimento')),
    detalhe   TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (prato, dimensao)
);
"""


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()

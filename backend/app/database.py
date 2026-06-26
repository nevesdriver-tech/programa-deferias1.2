from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


DB_PATH = Path(__file__).resolve().parent.parent / "programa_ferias.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS importacoes (
                id TEXT PRIMARY KEY,
                arquivo TEXT NOT NULL,
                aba TEXT NOT NULL,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS parametros (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                payload_json TEXT NOT NULL,
                atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS programacoes (
                id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                mensagem TEXT NOT NULL,
                payload_json TEXT,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def save_import(importacao_id: str, arquivo: str, aba: str, payload: dict[str, Any]) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO importacoes (id, arquivo, aba, payload_json) VALUES (?, ?, ?, ?)",
            (importacao_id, arquivo, aba, json.dumps(payload, ensure_ascii=False, default=str)),
        )
        conn.execute(
            "INSERT INTO logs (tipo, mensagem, payload_json) VALUES (?, ?, ?)",
            ("importacao", f"Importacao {arquivo} na aba {aba}", json.dumps({"id": importacao_id}, ensure_ascii=False)),
        )


def list_imports() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, arquivo, aba, criado_em FROM importacoes ORDER BY criado_em DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_import(importacao_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT payload_json FROM importacoes WHERE id = ?", (importacao_id,)).fetchone()
    return json.loads(row["payload_json"]) if row else None


def save_parametros(payload: list[dict[str, Any]]) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO parametros (id, payload_json, atualizado_em)
            VALUES (1, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                payload_json = excluded.payload_json,
                atualizado_em = CURRENT_TIMESTAMP
            """,
            (json.dumps(payload, ensure_ascii=False, default=str),),
        )


def load_parametros() -> list[dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT payload_json FROM parametros WHERE id = 1").fetchone()
    return json.loads(row["payload_json"]) if row else []


def save_programacoes(programacoes: list[dict[str, Any]]) -> None:
    with get_connection() as conn:
        for programacao in programacoes:
            conn.execute(
                """
                INSERT INTO programacoes (id, payload_json, atualizado_em)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    atualizado_em = CURRENT_TIMESTAMP
                """,
                (programacao["id"], json.dumps(programacao, ensure_ascii=False, default=str)),
            )


def list_programacoes() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT payload_json FROM programacoes ORDER BY atualizado_em DESC").fetchall()
    return [json.loads(row["payload_json"]) for row in rows]

from __future__ import annotations

import io
from typing import Any

import pandas as pd


def programacoes_to_excel(rows: list[dict[str, Any]]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        dataframe = pd.DataFrame(rows)
        dataframe.to_excel(writer, sheet_name="Programacao sugerida", index=False)
    output.seek(0)
    return output.read()


def programacoes_to_printable_html(rows: list[dict[str, Any]]) -> str:
    table_rows = "\n".join(
        "<tr>"
        + "".join(f"<td>{_escape(str(row.get(key, '')))}</td>" for key in row.keys())
        + "</tr>"
        for row in rows
    )
    headers = "".join(f"<th>{_escape(str(key))}</th>" for key in rows[0].keys()) if rows else ""
    return f"""
    <!doctype html>
    <html lang="pt-BR">
      <head>
        <meta charset="utf-8" />
        <title>Programacao de Ferias</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 32px; }}
          table {{ border-collapse: collapse; width: 100%; font-size: 12px; }}
          th, td {{ border: 1px solid #ddd; padding: 6px; text-align: left; }}
          th {{ background: #f3f4f6; }}
          @media print {{ button {{ display: none; }} }}
        </style>
      </head>
      <body>
        <button onclick="window.print()">Imprimir / salvar como PDF</button>
        <h1>Programacao de Ferias</h1>
        <table>
          <thead><tr>{headers}</tr></thead>
          <tbody>{table_rows}</tbody>
        </table>
      </body>
    </html>
    """


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )

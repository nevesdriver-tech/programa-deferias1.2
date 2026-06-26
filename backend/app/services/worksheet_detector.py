from __future__ import annotations

import io
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd


PREVIEW_ROWS = 8


def detect_worksheets(file_name: str, content: bytes, preview_rows: int = PREVIEW_ROWS) -> list[dict[str, Any]]:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".csv":
        dataframe = _read_csv(content)
        return [_worksheet_payload("CSV", dataframe, preview_rows)]

    excel = pd.ExcelFile(io.BytesIO(content))
    worksheets: list[dict[str, Any]] = []
    for sheet_name in excel.sheet_names:
        dataframe = pd.read_excel(excel, sheet_name=sheet_name, header=None, dtype=object)
        worksheets.append(_worksheet_payload(sheet_name, dataframe, preview_rows))
    return worksheets


def _read_csv(content: bytes) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "latin1"):
        try:
            return pd.read_csv(io.BytesIO(content), header=None, dtype=object, keep_default_na=False, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(io.BytesIO(content), header=None, dtype=object, keep_default_na=False)


def _worksheet_payload(sheet_name: str, dataframe: pd.DataFrame, preview_rows: int) -> dict[str, Any]:
    normalized = dataframe.where(pd.notna(dataframe), None)
    columns = [f"Coluna {index + 1}" for index in range(len(normalized.columns))]
    return {
        "sheetName": sheet_name,
        "rowCount": int(len(normalized.index)),
        "columns": columns,
        "preview": [
            _json_ready_row(row_number, columns, row)
            for row_number, row in enumerate(normalized.head(preview_rows).values.tolist(), start=1)
        ],
    }


def _json_ready_row(row_number: int, columns: list[str], row: list[Any]) -> dict[str, Any]:
    values = {"Linha": row_number}
    values.update({columns[index]: _json_ready_value(value) for index, value in enumerate(row)})
    return values


def _json_ready_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except ValueError:
            return str(value)
    return value

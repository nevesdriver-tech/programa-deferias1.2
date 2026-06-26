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
        dataframe = pd.read_excel(excel, sheet_name=sheet_name, dtype=object)
        worksheets.append(_worksheet_payload(sheet_name, dataframe, preview_rows))
    return worksheets


def _read_csv(content: bytes) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "latin1"):
        try:
            return pd.read_csv(io.BytesIO(content), dtype=object, keep_default_na=False, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(io.BytesIO(content), dtype=object, keep_default_na=False)


def _worksheet_payload(sheet_name: str, dataframe: pd.DataFrame, preview_rows: int) -> dict[str, Any]:
    normalized = dataframe.where(pd.notna(dataframe), None)
    return {
        "sheetName": sheet_name,
        "rowCount": int(len(normalized.index)),
        "columns": [str(column) for column in normalized.columns],
        "preview": [_json_ready_row(row) for row in normalized.head(preview_rows).to_dict(orient="records")],
    }


def _json_ready_row(row: dict[Any, Any]) -> dict[str, Any]:
    return {str(key): _json_ready_value(value) for key, value in row.items()}


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

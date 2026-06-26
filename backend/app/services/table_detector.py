from __future__ import annotations

import io
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


KNOWN_WORDS = {
    "cliente",
    "colaborador",
    "dias",
    "empresa",
    "escala",
    "ferias",
    "fim",
    "funcionario",
    "inicio",
    "matricula",
    "nome",
    "periodo",
    "posto",
    "saldo",
    "supervisor",
}


@dataclass
class WorksheetRows:
    sheet_name: str
    rows: list[list[Any]]


@dataclass
class SheetScore:
    worksheet: str
    header_row: int
    data_start_row: int
    last_row: int
    score: float
    header_score: float


def detect_main_table(file_name: str, content: bytes) -> dict[str, Any]:
    scores = [_score_sheet(worksheet) for worksheet in _read_worksheets(file_name, content)]
    if not scores:
        return {"worksheet": "", "headerRow": 0, "dataStartRow": 0, "lastRow": 0, "confidence": 0.0}

    ranked = sorted(scores, key=lambda item: item.score, reverse=True)
    best = ranked[0]
    second_score = ranked[1].score if len(ranked) > 1 else 0.0

    gap = (best.score - second_score) / best.score if best.score > 0 else 0.0
    header_strength = min(best.header_score / 25.0, 1.0)
    confidence = min(0.99, max(0.0, 0.45 + (gap * 0.35) + (header_strength * 0.2)))

    return {
        "worksheet": best.worksheet,
        "headerRow": best.header_row,
        "dataStartRow": best.data_start_row,
        "lastRow": best.last_row,
        "confidence": round(confidence, 2),
    }


def _read_worksheets(file_name: str, content: bytes) -> list[WorksheetRows]:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".csv":
        dataframe = _read_csv(content)
        return [WorksheetRows("CSV", _dataframe_rows(dataframe))]

    excel = pd.ExcelFile(io.BytesIO(content))
    worksheets: list[WorksheetRows] = []
    for sheet_name in excel.sheet_names:
        dataframe = pd.read_excel(excel, sheet_name=sheet_name, header=None, dtype=object)
        worksheets.append(WorksheetRows(sheet_name, _dataframe_rows(dataframe)))
    return worksheets


def _read_csv(content: bytes) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "latin1"):
        try:
            return pd.read_csv(io.BytesIO(content), header=None, dtype=object, keep_default_na=False, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(io.BytesIO(content), header=None, dtype=object, keep_default_na=False)


def _dataframe_rows(dataframe: pd.DataFrame) -> list[list[Any]]:
    normalized = dataframe.where(pd.notna(dataframe), None)
    return normalized.values.tolist()


def _score_sheet(worksheet: WorksheetRows) -> SheetScore:
    rows = worksheet.rows
    filled_counts = [_filled_count(row) for row in rows]
    filled_rows = sum(1 for count in filled_counts if count > 0)
    max_filled_columns = max(filled_counts, default=0)
    keyword_hits = sum(_keyword_hits(row) for row in rows)
    header_index, header_score = _detect_header_row(rows)
    last_index = _detect_last_used_row(rows)
    data_start_index = _detect_data_start_row(rows, header_index, last_index)

    score = (
        filled_rows * 0.4
        + max_filled_columns * 2.0
        + keyword_hits * 5.0
        + header_score * 8.0
    )

    return SheetScore(
        worksheet=worksheet.sheet_name,
        header_row=header_index + 1 if header_index >= 0 else 0,
        data_start_row=data_start_index + 1 if data_start_index >= 0 else 0,
        last_row=last_index + 1 if last_index >= 0 else 0,
        score=score,
        header_score=header_score,
    )


def _detect_header_row(rows: list[list[Any]]) -> tuple[int, float]:
    best_index = -1
    best_score = 0.0

    for index, row in enumerate(rows):
        filled = _filled_count(row)
        if filled < 2:
            continue

        keyword_hits = _keyword_hits(row)
        next_density = _following_data_density(rows, index)
        score = (keyword_hits * 4.0) + min(filled, 16) + (next_density * 2.0)

        if index <= 20:
            score += 2.0

        if score > best_score:
            best_index = index
            best_score = score

    return best_index, best_score


def _detect_data_start_row(rows: list[list[Any]], header_index: int, last_index: int) -> int:
    if header_index < 0:
        return -1

    for index in range(header_index + 1, last_index + 1):
        if _filled_count(rows[index]) > 0:
            return index
    return -1


def _detect_last_used_row(rows: list[list[Any]]) -> int:
    for index in range(len(rows) - 1, -1, -1):
        if _filled_count(rows[index]) > 0:
            return index
    return -1


def _following_data_density(rows: list[list[Any]], header_index: int) -> float:
    sample = rows[header_index + 1 : header_index + 6]
    if not sample:
        return 0.0

    filled_sample = [_filled_count(row) for row in sample if _filled_count(row) > 0]
    if not filled_sample:
        return 0.0
    return sum(filled_sample) / len(filled_sample)


def _filled_count(row: list[Any]) -> int:
    return sum(1 for value in row if _is_filled(value))


def _keyword_hits(row: list[Any]) -> int:
    text = " ".join(_normalize_text(value) for value in row if _is_filled(value))
    return sum(1 for word in KNOWN_WORDS if word in text)


def _is_filled(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _normalize_text(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", str(value).strip().lower())
    return "".join(character for character in normalized if not unicodedata.combining(character))

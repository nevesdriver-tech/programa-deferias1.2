from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile
from pydantic import BaseModel, Field

from .table_detector import detect_main_table
from .worksheet_detector import detect_worksheets


ALLOWED_EXTENSIONS = {".xls", ".xlsx", ".csv"}


class WorksheetPreview(BaseModel):
    sheetName: str
    rowCount: int
    columns: list[str] = Field(default_factory=list)
    preview: list[dict[str, Any]] = Field(default_factory=list)


class TableDetection(BaseModel):
    worksheet: str
    headerRow: int
    dataStartRow: int
    lastRow: int
    confidence: float


class ImportUploadResponse(BaseModel):
    fileName: str
    fileType: str
    worksheets: list[WorksheetPreview]
    tableDetection: TableDetection
    errors: list[str] = Field(default_factory=list)


async def import_preview_from_upload(file: UploadFile) -> ImportUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo sem nome.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Formato invalido. Envie .xls, .xlsx ou .csv.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")

    try:
        table_detection = detect_main_table(file.filename, content)
        preview_rows = max(8, int(table_detection.get("headerRow", 0)) + 5)
        worksheets = detect_worksheets(file.filename, content, preview_rows=preview_rows)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Nao foi possivel ler o arquivo: {exc}") from exc

    return ImportUploadResponse(
        fileName=file.filename,
        fileType=suffix.lstrip("."),
        worksheets=[WorksheetPreview(**worksheet) for worksheet in worksheets],
        tableDetection=TableDetection(**table_detection),
    )

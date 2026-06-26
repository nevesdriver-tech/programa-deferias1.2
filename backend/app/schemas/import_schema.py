from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


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

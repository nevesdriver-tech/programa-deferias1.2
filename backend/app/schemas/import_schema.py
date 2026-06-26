from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class WorksheetPreview(BaseModel):
    sheetName: str
    rowCount: int
    columns: list[str] = Field(default_factory=list)
    preview: list[dict[str, Any]] = Field(default_factory=list)


class ImportUploadResponse(BaseModel):
    fileName: str
    fileType: str
    worksheets: list[WorksheetPreview]
    errors: list[str] = Field(default_factory=list)

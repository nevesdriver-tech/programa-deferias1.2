from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from ..services.excel_import_service import ImportUploadResponse, import_preview_from_upload


router = APIRouter(prefix="/api/import", tags=["import"])


@router.post("/upload", response_model=ImportUploadResponse)
async def upload_import_file(file: UploadFile = File(...)) -> ImportUploadResponse:
    return await import_preview_from_upload(file)

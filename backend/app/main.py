from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response

from .database import (
    get_import,
    init_db,
    list_imports,
    list_programacoes,
    load_parametros,
    save_import,
    save_parametros,
    save_programacoes,
)
from .routes.import_routes import router as import_router
from .schemas import ImportResult, ManualMappingRequest, ParametroOperacional, SuggestionRequest
from .services.excel_reader import read_workbook, rows_to_domain
from .services.exporter import programacoes_to_excel, programacoes_to_printable_html
from .services.scheduler import generate_suggestions


app = FastAPI(title="Programa de Ferias API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(import_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/importar", response_model=ImportResult)
async def importar_planilha(
    file: UploadFile = File(...),
    sheet_name: str | None = Form(default=None),
) -> ImportResult:
    content = await file.read()
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo sem nome.")
    if not file.filename.lower().endswith((".xls", ".xlsx", ".csv")):
        raise HTTPException(status_code=400, detail="Formato invalido. Envie .xls, .xlsx ou .csv.")

    parsed = read_workbook(file.filename, content, sheet_name)
    colaboradores, periodos, row_errors = rows_to_domain(parsed.rows, parsed.mapping)
    parametros = [ParametroOperacional(**item) for item in load_parametros()] or [ParametroOperacional()]
    programacoes = generate_suggestions(colaboradores, periodos, parametros)
    importacao_id = str(uuid.uuid4())

    result = ImportResult(
        importacaoId=importacao_id,
        sheetName=parsed.sheet_name,
        availableSheets=parsed.available_sheets,
        detectedColumns=parsed.mapping,
        rows=parsed.rows,
        preview=parsed.preview,
        errors=parsed.errors + row_errors,
        colaboradores=colaboradores,
        periodos=periodos,
        programacoes=programacoes,
    )
    save_import(importacao_id, file.filename, parsed.sheet_name, result.model_dump())
    save_programacoes([programacao.model_dump() for programacao in programacoes])
    return result


@app.post("/importar/mapeamento-manual")
def importar_com_mapeamento_manual(request: ManualMappingRequest) -> dict[str, Any]:
    colaboradores, periodos, errors = rows_to_domain(request.rows, request.mapping)
    parametros = [ParametroOperacional(**item) for item in load_parametros()] or [ParametroOperacional()]
    programacoes = generate_suggestions(colaboradores, periodos, parametros)
    save_programacoes([programacao.model_dump() for programacao in programacoes])
    return {
        "errors": errors,
        "colaboradores": [item.model_dump() for item in colaboradores],
        "periodos": [item.model_dump() for item in periodos],
        "programacoes": [item.model_dump() for item in programacoes],
    }


@app.get("/importacoes")
def importacoes() -> list[dict[str, Any]]:
    return list_imports()


@app.get("/importacoes/{importacao_id}")
def obter_importacao(importacao_id: str) -> dict[str, Any]:
    payload = get_import(importacao_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Importacao nao encontrada.")
    return payload


@app.get("/parametros", response_model=list[ParametroOperacional])
def obter_parametros() -> list[ParametroOperacional]:
    payload = load_parametros()
    if not payload:
        return [ParametroOperacional()]
    return [ParametroOperacional(**item) for item in payload]


@app.put("/parametros", response_model=list[ParametroOperacional])
def atualizar_parametros(parametros: list[ParametroOperacional]) -> list[ParametroOperacional]:
    save_parametros([parametro.model_dump() for parametro in parametros])
    return parametros


@app.post("/programacoes/sugerir")
def sugerir_programacoes(request: SuggestionRequest) -> dict[str, Any]:
    parametros = request.parametros or [ParametroOperacional(**item) for item in load_parametros()] or [ParametroOperacional()]
    programacoes = generate_suggestions(request.colaboradores, request.periodos, parametros, request.inicioBusca)
    save_programacoes([programacao.model_dump() for programacao in programacoes])
    return {"programacoes": [programacao.model_dump() for programacao in programacoes]}


@app.get("/programacoes")
def obter_programacoes() -> list[dict[str, Any]]:
    return list_programacoes()


@app.post("/exportar/excel")
def exportar_excel(rows: list[dict[str, Any]]) -> Response:
    content = programacoes_to_excel(rows)
    return Response(
        content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="programacao-ferias.xlsx"'},
    )


@app.post("/exportar/pdf", response_class=HTMLResponse)
def exportar_pdf(rows: list[dict[str, Any]]) -> str:
    return programacoes_to_printable_html(rows)

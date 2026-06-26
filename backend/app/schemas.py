from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field


StatusProgramacao = Literal["OK", "Atenção", "Conflito", "Já programado", "Sem dados"]


class Colaborador(BaseModel):
    id: str
    codigo: str | None = None
    classe: str | None = None
    nome: str
    dataAdmissao: str | None = None
    posto: str | None = None
    turno: str | None = None
    escala: str | None = None
    observacoes: str | None = None


class PeriodoFerias(BaseModel):
    id: str
    colaboradorId: str
    venctoFerias: str | None = None
    feriasVencidas: str | None = None
    feriasProporcionais: str | None = None
    inicioAquisitivo: str | None = None
    fimAquisitivo: str | None = None
    inicioGozoAtual: str | None = None
    fimGozoAtual: str | None = None
    diasDireito: int | None = None
    diasGozados: int | None = None
    diasRestantes: int | None = None
    limiteGozo: str | None = None
    diasAfastado: int | None = None
    diasFaltas: int | None = None
    abono: str | None = None
    decimoTerceiro: str | None = None
    original: dict[str, Any] = Field(default_factory=dict)


class ProgramacaoSugerida(BaseModel):
    id: str
    periodoFeriasId: str
    inicioSugerido: str | None = None
    fimSugerido: str | None = None
    diasProgramados: int | None = None
    status: StatusProgramacao
    motivo: str
    conflitos: list[str] = Field(default_factory=list)


class ParametroOperacional(BaseModel):
    posto: str = "Geral"
    turno: str = "Geral"
    escala: str = "Geral"
    minimoAtivos: int = 1
    maximoFeriasSimultaneas: int = 1
    maximoGeralFeriasSimultaneas: int = 5
    colaboradoresIncompativeis: list[list[str]] = Field(default_factory=list)
    datasBloqueadas: list[str] = Field(default_factory=list)
    feristasDisponiveis: int = 0
    regraAbono: str = "Permitir conforme planilha"
    regraFracionamento: str = "Periodo unico"
    diasFeriasPadrao: int = 30
    antecedenciaMinimaDias: int = 30


class ImportResult(BaseModel):
    importacaoId: str
    sheetName: str
    availableSheets: list[str]
    detectedColumns: dict[str, str]
    rows: list[dict[str, Any]] = Field(default_factory=list)
    preview: list[dict[str, Any]]
    errors: list[str]
    colaboradores: list[Colaborador]
    periodos: list[PeriodoFerias]
    programacoes: list[ProgramacaoSugerida]


class ManualMappingRequest(BaseModel):
    importacaoId: str | None = None
    rows: list[dict[str, Any]]
    mapping: dict[str, str]


class SuggestionRequest(BaseModel):
    colaboradores: list[Colaborador]
    periodos: list[PeriodoFerias]
    parametros: list[ParametroOperacional] = Field(default_factory=list)
    inicioBusca: date | None = None

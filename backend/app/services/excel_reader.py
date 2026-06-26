from __future__ import annotations

import io
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .header_mapper import build_column_mapping, detect_header_rows
from .normalizer import clean_text, format_br_date, normalize_value, parse_int
from ..schemas import Colaborador, PeriodoFerias


TITLE_MARKER = "PROGRAMACAO DE FERIAS"


@dataclass
class ParsedSheet:
    sheet_name: str
    available_sheets: list[str]
    headers: list[str]
    mapping: dict[str, str]
    rows: list[dict[str, Any]]
    preview: list[dict[str, Any]]
    errors: list[str]


def _normalize_title(value: Any) -> str:
    from .normalizer import normalize_key

    return normalize_key(value).upper()


def read_workbook(file_name: str, content: bytes, selected_sheet: str | None = None) -> ParsedSheet:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".csv":
        dataframe = pd.read_csv(io.BytesIO(content), header=None, dtype=object, keep_default_na=False)
        raw_rows = dataframe.fillna("").values.tolist()
        parsed = _parse_raw_rows(raw_rows, "CSV", ["CSV"])
        return parsed

    excel = pd.ExcelFile(io.BytesIO(content))
    sheet_names = excel.sheet_names
    sheet_name = selected_sheet or _detect_vacation_sheet(excel, sheet_names)
    dataframe = pd.read_excel(excel, sheet_name=sheet_name, header=None, dtype=object)
    raw_rows = dataframe.fillna("").values.tolist()
    return _parse_raw_rows(raw_rows, sheet_name, sheet_names)


def _detect_vacation_sheet(excel: pd.ExcelFile, sheet_names: list[str]) -> str:
    for sheet_name in sheet_names:
        sample = pd.read_excel(excel, sheet_name=sheet_name, header=None, nrows=12, dtype=object).fillna("")
        text = " ".join(clean_text(value) for value in sample.values.flatten())
        if TITLE_MARKER in _normalize_title(text):
            return sheet_name
    return sheet_names[0]


def _parse_raw_rows(raw_rows: list[list[Any]], sheet_name: str, sheet_names: list[str]) -> ParsedSheet:
    if not raw_rows:
        return ParsedSheet(sheet_name, sheet_names, [], {}, [], [], ["Planilha sem linhas."])

    header_start, header_span = detect_header_rows(raw_rows)
    headers, mapping = build_column_mapping(raw_rows, header_start, header_span)
    data_rows = raw_rows[header_start + header_span :]
    rows: list[dict[str, Any]] = []

    for raw_row in data_rows:
        values = list(raw_row)[: len(headers)]
        values.extend([""] * max(0, len(headers) - len(values)))
        row = {headers[index]: normalize_value(value) for index, value in enumerate(values)}
        if any(value is not None for value in row.values()):
            rows.append(row)

    errors: list[str] = []
    required = ["codigo", "nome", "inicioAquisitivo", "fimAquisitivo", "limiteGozo"]
    missing = [field for field in required if field not in mapping]
    if missing:
        errors.append("Campos essenciais nao detectados automaticamente: " + ", ".join(missing))

    return ParsedSheet(sheet_name, sheet_names, headers, mapping, rows, rows[:8], errors)


def rows_to_domain(rows: list[dict[str, Any]], mapping: dict[str, str]) -> tuple[list[Colaborador], list[PeriodoFerias], list[str]]:
    colaboradores: list[Colaborador] = []
    periodos: list[PeriodoFerias] = []
    errors: list[str] = []
    colaborador_by_key: dict[str, Colaborador] = {}
    previous_colaborador: Colaborador | None = None

    for index, row in enumerate(rows, start=1):
        data = _mapped_row(row, mapping)
        codigo = clean_text(data.get("codigo"))
        nome = clean_text(data.get("nome"))
        has_period = any(data.get(field) for field in ("inicioAquisitivo", "fimAquisitivo", "limiteGozo", "venctoFerias"))

        if not codigo and not nome and not has_period:
            continue

        if not codigo and not nome and previous_colaborador and has_period:
            colaborador = previous_colaborador
        elif nome:
            key = codigo or nome.upper()
            colaborador = colaborador_by_key.get(key)
            if not colaborador:
                colaborador = Colaborador(
                    id=str(uuid.uuid4()),
                    codigo=codigo or None,
                    classe=clean_text(data.get("classe")) or None,
                    nome=nome,
                    dataAdmissao=format_br_date(data.get("dataAdmissao")),
                    posto=clean_text(data.get("posto")) or None,
                    turno=clean_text(data.get("turno")) or None,
                    escala=clean_text(data.get("escala")) or None,
                )
                colaborador_by_key[key] = colaborador
                colaboradores.append(colaborador)
            previous_colaborador = colaborador
        else:
            errors.append(f"Linha {index}: colaborador sem codigo ou nome.")
            continue

        periodo = PeriodoFerias(
            id=str(uuid.uuid4()),
            colaboradorId=colaborador.id,
            venctoFerias=format_br_date(data.get("venctoFerias")),
            feriasVencidas=clean_text(data.get("feriasVencidas")) or None,
            feriasProporcionais=clean_text(data.get("feriasProporcionais")) or None,
            inicioAquisitivo=format_br_date(data.get("inicioAquisitivo")),
            fimAquisitivo=format_br_date(data.get("fimAquisitivo")),
            inicioGozoAtual=format_br_date(data.get("inicioGozoAtual")),
            fimGozoAtual=format_br_date(data.get("fimGozoAtual")),
            diasDireito=parse_int(data.get("diasDireito")),
            diasGozados=parse_int(data.get("diasGozados")),
            diasRestantes=parse_int(data.get("diasRestantes")),
            limiteGozo=format_br_date(data.get("limiteGozo")),
            diasAfastado=parse_int(data.get("diasAfastado")),
            diasFaltas=parse_int(data.get("diasFaltas")),
            abono=clean_text(data.get("abono")) or None,
            decimoTerceiro=clean_text(data.get("decimoTerceiro")) or None,
            original=row,
        )
        periodos.append(periodo)

    return colaboradores, periodos, errors


def _mapped_row(row: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    return {field: row.get(column_name) for field, column_name in mapping.items()}

from __future__ import annotations

from collections.abc import Iterable

from .normalizer import clean_text, normalize_key


CANONICAL_FIELDS: dict[str, list[str]] = {
    "codigo": ["codigo", "cod"],
    "classe": ["classe"],
    "nome": ["empregado", "colaborador", "nome"],
    "dataAdmissao": ["data admissao", "admissao"],
    "venctoFerias": ["vencto ferias", "venc ferias", "vencimento ferias"],
    "feriasVencidas": ["fer venc", "ferias vencidas", "ferias venc"],
    "feriasProporcionais": ["fer pro", "ferias proporcionais", "ferias prop"],
    "inicioAquisitivo": ["inicio aquisitivo", "ini aquisitivo"],
    "fimAquisitivo": ["fim aquisitivo"],
    "inicioGozoAtual": ["inicio gozo ferias", "inicio gozo", "inicio ferias"],
    "fimGozoAtual": ["fim gozo ferias", "fim gozo", "fim ferias"],
    "dias": ["dias"],
    "abono": ["abono"],
    "decimoTerceiro": ["13", "13 terceiro", "decimo terceiro"],
    "diasDireito": ["dias dir", "dias direito"],
    "diasGozados": ["dias goz", "dias gozados"],
    "diasRestantes": ["dias rest", "dias restantes"],
    "limiteGozo": ["limite p/ gozo", "limite p gozo", "limite para gozo", "limite gozo"],
    "diasAfastado": ["dias afast", "dias afastados"],
    "diasFaltas": ["dias faltas", "faltas"],
    "posto": ["posto", "unidade", "lotacao"],
    "turno": ["turno"],
    "escala": ["escala"],
}

EXPECTED_TERMS = {
    "codigo",
    "classe",
    "empregado",
    "data",
    "admissao",
    "vencto",
    "ferias",
    "aquisitivo",
    "gozo",
    "limite",
    "dias",
}


def combine_header_parts(parts: Iterable[object]) -> str:
    values: list[str] = []
    for part in parts:
        text = clean_text(part)
        if text and text not in values:
            values.append(text)
    return " ".join(values)


def match_field(header: str) -> str | None:
    normalized = normalize_key(header)
    if not normalized:
        return None

    best_field: str | None = None
    best_score = 0
    for field, aliases in CANONICAL_FIELDS.items():
        for alias in aliases:
            alias_norm = normalize_key(alias)
            if normalized == alias_norm:
                return field
            if alias_norm and alias_norm in normalized:
                score = len(alias_norm)
                if score > best_score:
                    best_score = score
                    best_field = field
    return best_field


def detect_header_rows(raw_rows: list[list[object]], max_scan_rows: int = 20) -> tuple[int, int]:
    best_index = 0
    best_score = -1
    best_span = 1
    limit = min(len(raw_rows), max_scan_rows)

    for start in range(limit):
        for span in range(1, min(4, limit - start) + 1):
            combined_columns = zip(*raw_rows[start : start + span])
            detected = 0
            terms = 0
            for column_parts in combined_columns:
                header = combine_header_parts(column_parts)
                normalized = normalize_key(header)
                if match_field(header):
                    detected += 3
                terms += sum(1 for term in EXPECTED_TERMS if term in normalized)
            score = detected + terms
            if score > best_score:
                best_score = score
                best_index = start
                best_span = span

    return best_index, best_span


def build_column_mapping(raw_rows: list[list[object]], header_start: int, header_span: int) -> tuple[list[str], dict[str, str]]:
    header_rows = raw_rows[header_start : header_start + header_span]
    headers: list[str] = []
    mapping: dict[str, str] = {}
    used: set[str] = set()

    for index, parts in enumerate(zip(*header_rows)):
        header = combine_header_parts(parts) or f"Coluna {index + 1}"
        original_header = header
        suffix = 2
        while header in used:
            header = f"{original_header} {suffix}"
            suffix += 1
        used.add(header)
        headers.append(header)

        field = match_field(header)
        if field and field not in mapping:
            mapping[field] = header

    return headers, mapping

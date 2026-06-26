from __future__ import annotations

import uuid
from datetime import date, timedelta

from ..schemas import Colaborador, ParametroOperacional, PeriodoFerias, ProgramacaoSugerida
from .normalizer import add_days, date_range_overlaps, format_br_date, parse_date


def generate_suggestions(
    colaboradores: list[Colaborador],
    periodos: list[PeriodoFerias],
    parametros: list[ParametroOperacional],
    inicio_busca: date | None = None,
) -> list[ProgramacaoSugerida]:
    colaborador_map = {colaborador.id: colaborador for colaborador in colaboradores}
    scheduled: list[tuple[str, str, str, date, date]] = []
    today = date.today()
    start_search = inicio_busca or today

    sorted_periodos = sorted(
        periodos,
        key=lambda periodo: (
            not _is_overdue(periodo, today),
            parse_date(periodo.limiteGozo) or date.max,
            -(periodo.diasRestantes or 0),
            parse_date(colaborador_map.get(periodo.colaboradorId).dataAdmissao if colaborador_map.get(periodo.colaboradorId) else None)
            or date.max,
        ),
    )

    result: list[ProgramacaoSugerida] = []
    for periodo in sorted_periodos:
        colaborador = colaborador_map.get(periodo.colaboradorId)
        suggestion = _suggest_for_period(periodo, colaborador, parametros, scheduled, start_search)
        result.append(suggestion)

        if suggestion.inicioSugerido and suggestion.fimSugerido and colaborador and suggestion.status in {"OK", "Atenção"}:
            scheduled.append(
                (
                    colaborador.id,
                    colaborador.posto or "Geral",
                    colaborador.turno or "Geral",
                    parse_date(suggestion.inicioSugerido),
                    parse_date(suggestion.fimSugerido),
                )
            )

    return result


def _suggest_for_period(
    periodo: PeriodoFerias,
    colaborador: Colaborador | None,
    parametros: list[ParametroOperacional],
    scheduled: list[tuple[str, str, str, date, date]],
    start_search: date,
) -> ProgramacaoSugerida:
    base_id = str(uuid.uuid4())
    if not colaborador:
        return ProgramacaoSugerida(id=base_id, periodoFeriasId=periodo.id, status="Sem dados", motivo="Colaborador nao encontrado.")

    if periodo.inicioGozoAtual and periodo.fimGozoAtual:
        return ProgramacaoSugerida(
            id=base_id,
            periodoFeriasId=periodo.id,
            inicioSugerido=periodo.inicioGozoAtual,
            fimSugerido=periodo.fimGozoAtual,
            diasProgramados=periodo.diasRestantes or periodo.diasDireito,
            status="Já programado",
            motivo="Planilha ja possui inicio e fim de gozo preenchidos.",
        )

    missing = []
    if not periodo.inicioAquisitivo:
        missing.append("inicio aquisitivo")
    if not periodo.fimAquisitivo:
        missing.append("fim aquisitivo")
    if not periodo.limiteGozo:
        missing.append("limite para gozo")
    if not periodo.diasRestantes:
        missing.append("dias restantes")
    if missing:
        return ProgramacaoSugerida(
            id=base_id,
            periodoFeriasId=periodo.id,
            status="Sem dados",
            motivo="Campos essenciais ausentes: " + ", ".join(missing) + ".",
            conflitos=missing,
        )

    limite = parse_date(periodo.limiteGozo)
    if not limite:
        return ProgramacaoSugerida(
            id=base_id,
            periodoFeriasId=periodo.id,
            status="Sem dados",
            motivo="Limite para gozo invalido.",
            conflitos=["limite para gozo invalido"],
        )

    parametro = _select_parametro(colaborador, parametros)
    dias = min(periodo.diasRestantes or parametro.diasFeriasPadrao, parametro.diasFeriasPadrao)
    first_day = max(start_search + timedelta(days=parametro.antecedenciaMinimaDias), date.today())
    conflicts_seen: set[str] = set()

    cursor = first_day
    while cursor <= limite:
        end = add_days(cursor, dias)
        if end > limite:
            conflicts_seen.add("janela ultrapassa o limite para gozo")
            break

        conflicts = _validate_window(colaborador, parametro, scheduled, cursor, end)
        if not conflicts:
            status = "Atenção" if (limite - cursor).days <= 30 else "OK"
            motivo = "Janela sugerida respeita as regras cadastradas."
            if status == "Atenção":
                motivo = "Janela valida, mas proxima do limite para gozo."
            return ProgramacaoSugerida(
                id=base_id,
                periodoFeriasId=periodo.id,
                inicioSugerido=format_br_date(cursor),
                fimSugerido=format_br_date(end),
                diasProgramados=dias,
                status=status,
                motivo=motivo,
            )

        conflicts_seen.update(conflicts)
        cursor += timedelta(days=1)

    return ProgramacaoSugerida(
        id=base_id,
        periodoFeriasId=periodo.id,
        status="Conflito",
        motivo="Nao foi encontrada janela valida sem quebrar as regras cadastradas.",
        conflitos=sorted(conflicts_seen) or ["sem janela disponivel ate o limite"],
    )


def _validate_window(
    colaborador: Colaborador,
    parametro: ParametroOperacional,
    scheduled: list[tuple[str, str, str, date, date]],
    start: date,
    end: date,
) -> list[str]:
    conflicts: list[str] = []
    blocked_dates = [parse_date(value) for value in parametro.datasBloqueadas]
    if any(blocked and start <= blocked <= end for blocked in blocked_dates):
        conflicts.append("periodo contem data bloqueada")

    same_post = [
        item
        for item in scheduled
        if item[1] == (colaborador.posto or "Geral") and date_range_overlaps(start, end, item[3], item[4])
    ]
    same_general = [item for item in scheduled if date_range_overlaps(start, end, item[3], item[4])]

    if len(same_post) >= parametro.maximoFeriasSimultaneas:
        conflicts.append("limite de ferias simultaneas no posto excedido")
    if len(same_general) >= parametro.maximoGeralFeriasSimultaneas:
        conflicts.append("limite geral de ferias simultaneas excedido")

    incompatible_ids = {
        other_id
        for pair in parametro.colaboradoresIncompativeis
        if colaborador.id in pair
        for other_id in pair
        if other_id != colaborador.id
    }
    if any(item[0] in incompatible_ids and date_range_overlaps(start, end, item[3], item[4]) for item in scheduled):
        conflicts.append("colaborador incompativel no mesmo periodo")

    return conflicts


def _select_parametro(colaborador: Colaborador, parametros: list[ParametroOperacional]) -> ParametroOperacional:
    if not parametros:
        return ParametroOperacional()

    def score(parametro: ParametroOperacional) -> int:
        return sum(
            [
                parametro.posto in {colaborador.posto, "Geral"},
                parametro.turno in {colaborador.turno, "Geral"},
                parametro.escala in {colaborador.escala, "Geral"},
            ]
        )

    return max(parametros, key=score)


def _is_overdue(periodo: PeriodoFerias, today: date) -> bool:
    limite = parse_date(periodo.limiteGozo)
    return bool(periodo.feriasVencidas) or (limite is not None and limite <= today)

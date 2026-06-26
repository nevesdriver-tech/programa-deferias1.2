"use client";

import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import interactionPlugin from "@fullcalendar/interaction";
import { useEffect, useMemo, useState } from "react";
import {
  aplicarMapeamentoManual,
  carregarParametros,
  exportar,
  importarPlanilha,
  salvarParametros,
  sugerirProgramacoes,
} from "../lib/api";
import type { Colaborador, ImportResult, ParametroOperacional, PeriodoFerias, ProgramacaoSugerida } from "../lib/types";

type FilterState = {
  posto: string;
  turno: string;
  escala: string;
  status: string;
};

const REQUIRED_FIELDS = [
  "codigo",
  "classe",
  "nome",
  "dataAdmissao",
  "venctoFerias",
  "feriasVencidas",
  "feriasProporcionais",
  "inicioAquisitivo",
  "fimAquisitivo",
  "inicioGozoAtual",
  "fimGozoAtual",
  "diasDireito",
  "diasGozados",
  "diasRestantes",
  "limiteGozo",
  "diasAfastado",
  "diasFaltas",
  "posto",
  "turno",
  "escala",
];

const DEFAULT_PARAMETRO: ParametroOperacional = {
  posto: "Geral",
  turno: "Geral",
  escala: "Geral",
  minimoAtivos: 1,
  maximoFeriasSimultaneas: 1,
  maximoGeralFeriasSimultaneas: 5,
  colaboradoresIncompativeis: [],
  datasBloqueadas: [],
  feristasDisponiveis: 0,
  regraAbono: "Permitir conforme planilha",
  regraFracionamento: "Periodo unico",
  diasFeriasPadrao: 30,
  antecedenciaMinimaDias: 30,
};

export default function Home() {
  const [tab, setTab] = useState("importacao");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [colaboradores, setColaboradores] = useState<Colaborador[]>([]);
  const [periodos, setPeriodos] = useState<PeriodoFerias[]>([]);
  const [programacoes, setProgramacoes] = useState<ProgramacaoSugerida[]>([]);
  const [parametros, setParametros] = useState<ParametroOperacional[]>([DEFAULT_PARAMETRO]);
  const [manualMapping, setManualMapping] = useState<Record<string, string>>({});
  const [filters, setFilters] = useState({ posto: "", turno: "", escala: "", status: "" });

  useEffect(() => {
    carregarParametros()
      .then((data) => setParametros(data.length ? data : [DEFAULT_PARAMETRO]))
      .catch(() => setParametros([DEFAULT_PARAMETRO]));
  }, []);

  const colaboradorMap = useMemo(
    () => new Map(colaboradores.map((colaborador) => [colaborador.id, colaborador])),
    [colaboradores],
  );

  const periodoMap = useMemo(() => new Map(periodos.map((periodo) => [periodo.id, periodo])), [periodos]);

  const enrichedRows = useMemo(() => {
    return programacoes.map((programacao) => {
      const periodo = periodoMap.get(programacao.periodoFeriasId);
      const colaborador = periodo ? colaboradorMap.get(periodo.colaboradorId) : undefined;
      return {
        programacaoId: programacao.id,
        codigo: colaborador?.codigo ?? "",
        classe: colaborador?.classe ?? "",
        empregado: colaborador?.nome ?? "",
        posto: colaborador?.posto ?? "",
        turno: colaborador?.turno ?? "",
        escala: colaborador?.escala ?? "",
        dataAdmissao: colaborador?.dataAdmissao ?? "",
        inicioAquisitivo: periodo?.inicioAquisitivo ?? "",
        fimAquisitivo: periodo?.fimAquisitivo ?? "",
        limiteGozo: periodo?.limiteGozo ?? "",
        diasDireito: periodo?.diasDireito ?? "",
        diasGozados: periodo?.diasGozados ?? "",
        diasRestantes: periodo?.diasRestantes ?? "",
        inicioSugerido: programacao.inicioSugerido ?? "",
        fimSugerido: programacao.fimSugerido ?? "",
        status: programacao.status,
        motivo: programacao.motivo,
      };
    });
  }, [colaboradorMap, periodoMap, programacoes]);

  const filteredRows = enrichedRows.filter((row) => {
    return (
      (!filters.posto || row.posto === filters.posto) &&
      (!filters.turno || row.turno === filters.turno) &&
      (!filters.escala || row.escala === filters.escala) &&
      (!filters.status || row.status === filters.status)
    );
  });

  async function handleImport(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const file = form.get("file");
    if (!(file instanceof File) || !file.name) {
      setMessage("Selecione uma planilha.");
      return;
    }
    setLoading(true);
    setMessage("Importando planilha...");
    try {
      const result = await importarPlanilha(file);
      setImportResult(result);
      setColaboradores(result.colaboradores);
      setPeriodos(result.periodos);
      setProgramacoes(result.programacoes);
      setManualMapping(result.detectedColumns);
      setMessage(`Importacao concluida: ${result.colaboradores.length} colaboradores e ${result.periodos.length} periodos.`);
      setTab("programacao");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Falha ao importar.");
    } finally {
      setLoading(false);
    }
  }

  async function handleManualMapping() {
    if (!importResult) return;
    setLoading(true);
    try {
      const result = await aplicarMapeamentoManual(importResult.rows, manualMapping);
      setColaboradores(result.colaboradores);
      setPeriodos(result.periodos);
      setProgramacoes(result.programacoes);
      setMessage(`Mapeamento aplicado com ${result.errors.length} aviso(s).`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Falha ao aplicar mapeamento.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveParametros() {
    setLoading(true);
    try {
      const saved = await salvarParametros(parametros);
      setParametros(saved);
      if (colaboradores.length && periodos.length) {
        const result = await sugerirProgramacoes(colaboradores, periodos, saved);
        setProgramacoes(result.programacoes);
      }
      setMessage("Parametros salvos e programacao recalculada.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Falha ao salvar parametros.");
    } finally {
      setLoading(false);
    }
  }

  async function handleExport(kind: "excel" | "pdf") {
    const blob = await exportar(kind === "excel" ? "/exportar/excel" : "/exportar/pdf", filteredRows);
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
  }

  return (
    <main className="container">
      <section className="hero">
        <h1>Programa de Ferias</h1>
        <p>Importe planilhas com cabecalhos quebrados, configure regras de cobertura e gere uma previa editavel.</p>
      </section>

      <nav className="tabs">
        {["importacao", "parametros", "programacao", "calendario"].map((item) => (
          <button className={tab === item ? "active" : ""} key={item} onClick={() => setTab(item)}>
            {item[0].toUpperCase() + item.slice(1)}
          </button>
        ))}
      </nav>

      {message && <div className="card muted">{loading ? "Carregando... " : null}{message}</div>}

      {tab === "importacao" && (
        <ImportacaoTab
          importResult={importResult}
          manualMapping={manualMapping}
          onImport={handleImport}
          onMappingChange={setManualMapping}
          onApplyMapping={handleManualMapping}
        />
      )}

      {tab === "parametros" && (
        <ParametrosTab parametros={parametros} setParametros={setParametros} onSave={handleSaveParametros} />
      )}

      {tab === "programacao" && (
        <ProgramacaoTab
          rows={filteredRows}
          programacoes={programacoes}
          setProgramacoes={setProgramacoes}
          filters={filters}
          setFilters={setFilters}
          onExport={handleExport}
        />
      )}

      {tab === "calendario" && (
        <CalendarioTab rows={filteredRows} filters={filters} setFilters={setFilters} />
      )}
    </main>
  );
}

function ImportacaoTab({
  importResult,
  manualMapping,
  onImport,
  onMappingChange,
  onApplyMapping,
}: {
  importResult: ImportResult | null;
  manualMapping: Record<string, string>;
  onImport: (event: React.FormEvent<HTMLFormElement>) => void;
  onMappingChange: (mapping: Record<string, string>) => void;
  onApplyMapping: () => void;
}) {
  const headers = importResult?.preview[0] ? Object.keys(importResult.preview[0]) : [];

  return (
    <section className="grid two">
      <div className="card stack">
        <h2>Importacao</h2>
        <form className="stack" onSubmit={onImport}>
          <input accept=".xls,.xlsx,.csv" name="file" type="file" />
          <button type="submit">Importar planilha</button>
        </form>
        {importResult && (
          <>
            <p className="muted">Aba detectada: {importResult.sheetName}</p>
            <p className="muted">Abas disponiveis: {importResult.availableSheets.join(", ")}</p>
            {!!importResult.errors.length && (
              <div className="errors">
                {importResult.errors.map((error) => (
                  <p key={error}>{error}</p>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      <div className="card stack">
        <h2>Mapeamento de colunas</h2>
        {!importResult ? (
          <p className="muted">Importe uma planilha para ver o mapeamento automatico.</p>
        ) : (
          <>
            <div className="row">
              {REQUIRED_FIELDS.map((field) => (
                <label key={field}>
                  {field}
                  <select
                    value={manualMapping[field] ?? ""}
                    onChange={(event) => onMappingChange({ ...manualMapping, [field]: event.target.value })}
                  >
                    <option value="">Nao mapear</option>
                    {headers.map((header) => (
                      <option key={header} value={header}>
                        {header}
                      </option>
                    ))}
                  </select>
                </label>
              ))}
            </div>
            <button onClick={onApplyMapping}>Aplicar mapeamento manual</button>
          </>
        )}
      </div>

      <div className="card" style={{ gridColumn: "1 / -1" }}>
        <h2>Previa das primeiras linhas</h2>
        <PreviewTable rows={importResult?.preview ?? []} />
      </div>
    </section>
  );
}

function ParametrosTab({
  parametros,
  setParametros,
  onSave,
}: {
  parametros: ParametroOperacional[];
  setParametros: (parametros: ParametroOperacional[]) => void;
  onSave: () => void;
}) {
  function update(index: number, patch: Partial<ParametroOperacional>) {
    setParametros(parametros.map((parametro, itemIndex) => (itemIndex === index ? { ...parametro, ...patch } : parametro)));
  }

  return (
    <section className="card stack">
      <h2>Parametros operacionais</h2>
      {parametros.map((parametro, index) => (
        <div className="card stack" key={`${parametro.posto}-${index}`}>
          <div className="row">
            <label>Posto<input value={parametro.posto} onChange={(event) => update(index, { posto: event.target.value })} /></label>
            <label>Turno<input value={parametro.turno} onChange={(event) => update(index, { turno: event.target.value })} /></label>
            <label>Escala<input value={parametro.escala} onChange={(event) => update(index, { escala: event.target.value })} /></label>
            <label>Minimo ativos<input type="number" value={parametro.minimoAtivos} onChange={(event) => update(index, { minimoAtivos: Number(event.target.value) })} /></label>
            <label>Max. ferias no posto<input type="number" value={parametro.maximoFeriasSimultaneas} onChange={(event) => update(index, { maximoFeriasSimultaneas: Number(event.target.value) })} /></label>
            <label>Max. geral<input type="number" value={parametro.maximoGeralFeriasSimultaneas} onChange={(event) => update(index, { maximoGeralFeriasSimultaneas: Number(event.target.value) })} /></label>
            <label>Dias padrao<input type="number" value={parametro.diasFeriasPadrao} onChange={(event) => update(index, { diasFeriasPadrao: Number(event.target.value) })} /></label>
            <label>Antecedencia minima<input type="number" value={parametro.antecedenciaMinimaDias} onChange={(event) => update(index, { antecedenciaMinimaDias: Number(event.target.value) })} /></label>
          </div>
          <div className="row">
            <label>Datas bloqueadas<textarea value={parametro.datasBloqueadas.join("\n")} onChange={(event) => update(index, { datasBloqueadas: event.target.value.split("\n").filter(Boolean) })} /></label>
            <label>Regra de abono<textarea value={parametro.regraAbono} onChange={(event) => update(index, { regraAbono: event.target.value })} /></label>
            <label>Regra de fracionamento<textarea value={parametro.regraFracionamento} onChange={(event) => update(index, { regraFracionamento: event.target.value })} /></label>
          </div>
        </div>
      ))}
      <div className="row">
        <button className="secondary" onClick={() => setParametros([...parametros, DEFAULT_PARAMETRO])}>Adicionar regra</button>
        <button onClick={onSave}>Salvar parametros e recalcular</button>
      </div>
    </section>
  );
}

function ProgramacaoTab({
  rows,
  programacoes,
  setProgramacoes,
  filters,
  setFilters,
  onExport,
}: {
  rows: Record<string, unknown>[];
  programacoes: ProgramacaoSugerida[];
  setProgramacoes: (programacoes: ProgramacaoSugerida[]) => void;
  filters: FilterState;
  setFilters: (filters: FilterState) => void;
  onExport: (kind: "excel" | "pdf") => void;
}) {
  return (
    <section className="card stack">
      <h2>Programacao sugerida</h2>
      <Filters rows={rows} filters={filters} setFilters={setFilters} />
      <div className="row">
        <button onClick={() => onExport("excel")}>Exportar Excel</button>
        <button className="secondary" onClick={() => onExport("pdf")}>Gerar PDF</button>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {["Codigo", "Classe", "Empregado", "Posto", "Turno", "Escala", "Admissao", "Inicio aquisitivo", "Fim aquisitivo", "Limite", "Direito", "Gozados", "Restantes", "Inicio sugerido", "Fim sugerido", "Status", "Motivo"].map((header) => (
                <th key={header}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={`${row.codigo}-${row.inicioAquisitivo}-${index}`}>
                <td>{String(row.codigo)}</td>
                <td>{String(row.classe)}</td>
                <td>{String(row.empregado)}</td>
                <td>{String(row.posto)}</td>
                <td>{String(row.turno)}</td>
                <td>{String(row.escala)}</td>
                <td>{String(row.dataAdmissao)}</td>
                <td>{String(row.inicioAquisitivo)}</td>
                <td>{String(row.fimAquisitivo)}</td>
                <td>{String(row.limiteGozo)}</td>
                <td>{String(row.diasDireito)}</td>
                <td>{String(row.diasGozados)}</td>
                <td>{String(row.diasRestantes)}</td>
                <td><input value={String(row.inicioSugerido)} onChange={(event) => updateProgramacao(String(row.programacaoId), { inicioSugerido: event.target.value }, programacoes, setProgramacoes)} /></td>
                <td><input value={String(row.fimSugerido)} onChange={(event) => updateProgramacao(String(row.programacaoId), { fimSugerido: event.target.value }, programacoes, setProgramacoes)} /></td>
                <td><StatusBadge status={String(row.status)} /></td>
                <td>{String(row.motivo)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function CalendarioTab({
  rows,
  filters,
  setFilters,
}: {
  rows: Record<string, unknown>[];
  filters: FilterState;
  setFilters: (filters: FilterState) => void;
}) {
  const events = rows
    .filter((row) => row.inicioSugerido && row.fimSugerido)
    .map((row) => ({
      title: `${row.empregado} - ${row.status}`,
      start: brDateToIso(String(row.inicioSugerido)),
      end: addOneDayIso(String(row.fimSugerido)),
      color: eventColor(String(row.status)),
    }));

  return (
    <section className="card stack">
      <h2>Calendario</h2>
      <Filters rows={rows} filters={filters} setFilters={setFilters} />
      <FullCalendar plugins={[dayGridPlugin, interactionPlugin]} initialView="dayGridMonth" locale="pt-br" events={events} height="auto" />
    </section>
  );
}

function Filters({
  rows,
  filters,
  setFilters,
}: {
  rows: Record<string, unknown>[];
  filters: FilterState;
  setFilters: (filters: FilterState) => void;
}) {
  return (
    <div className="row">
      {(["posto", "turno", "escala", "status"] as const).map((field) => (
        <label key={field}>
          Filtrar por {field}
          <select value={filters[field] ?? ""} onChange={(event) => setFilters({ ...filters, [field]: event.target.value })}>
            <option value="">Todos</option>
            {unique(rows.map((row) => String(row[field] ?? "")).filter(Boolean)).map((value) => (
              <option key={value} value={value}>{value}</option>
            ))}
          </select>
        </label>
      ))}
    </div>
  );
}

function PreviewTable({ rows }: { rows: Record<string, unknown>[] }) {
  if (!rows.length) return <p className="muted">Nenhuma linha para exibir.</p>;
  const headers = Object.keys(rows[0]);
  return (
    <div className="table-wrap">
      <table>
        <thead><tr>{headers.map((header) => <th key={header}>{header}</th>)}</tr></thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>{headers.map((header) => <td key={header}>{String(row[header] ?? "")}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const className =
    {
      OK: "OK",
      Atenção: "Atencao",
      Conflito: "Conflito",
      "Já programado": "JaProgramado",
      "Sem dados": "SemDados",
    }[status] ?? "SemDados";
  return <span className={`badge ${className}`}>{status}</span>;
}

function updateProgramacao(
  id: string,
  patch: Partial<ProgramacaoSugerida>,
  programacoes: ProgramacaoSugerida[],
  setProgramacoes: (programacoes: ProgramacaoSugerida[]) => void,
) {
  setProgramacoes(programacoes.map((programacao) => (programacao.id === id ? { ...programacao, ...patch } : programacao)));
}

function unique(values: string[]) {
  return Array.from(new Set(values)).sort();
}

function brDateToIso(value: string) {
  const [day, month, year] = value.split("/");
  return year && month && day ? `${year}-${month}-${day}` : value;
}

function addOneDayIso(value: string) {
  const iso = brDateToIso(value);
  const date = new Date(`${iso}T00:00:00`);
  date.setDate(date.getDate() + 1);
  return date.toISOString().slice(0, 10);
}

function eventColor(status: string) {
  if (status === "Conflito") return "#dc2626";
  if (status === "Atenção") return "#d97706";
  if (status === "Já programado") return "#2563eb";
  if (status === "Sem dados") return "#64748b";
  return "#16a34a";
}

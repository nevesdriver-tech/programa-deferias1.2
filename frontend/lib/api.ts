import type { Colaborador, ImportResult, ParametroOperacional, PeriodoFerias, ProgramacaoSugerida } from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Erro ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function importarPlanilha(file: File, sheetName?: string): Promise<ImportResult> {
  const form = new FormData();
  form.append("file", file);
  if (sheetName) {
    form.append("sheet_name", sheetName);
  }
  return request<ImportResult>("/importar", {
    method: "POST",
    body: form,
  });
}

export async function carregarParametros(): Promise<ParametroOperacional[]> {
  return request<ParametroOperacional[]>("/parametros");
}

export async function salvarParametros(parametros: ParametroOperacional[]): Promise<ParametroOperacional[]> {
  return request<ParametroOperacional[]>("/parametros", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(parametros),
  });
}

export async function sugerirProgramacoes(
  colaboradores: Colaborador[],
  periodos: PeriodoFerias[],
  parametros: ParametroOperacional[],
): Promise<{ programacoes: ProgramacaoSugerida[] }> {
  return request<{ programacoes: ProgramacaoSugerida[] }>("/programacoes/sugerir", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ colaboradores, periodos, parametros }),
  });
}

export async function aplicarMapeamentoManual(
  rows: Record<string, unknown>[],
  mapping: Record<string, string>,
): Promise<{
  errors: string[];
  colaboradores: Colaborador[];
  periodos: PeriodoFerias[];
  programacoes: ProgramacaoSugerida[];
}> {
  return request("/importar/mapeamento-manual", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rows, mapping }),
  });
}

export async function exportar(path: "/exportar/excel" | "/exportar/pdf", rows: Record<string, unknown>[]): Promise<Blob> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(rows),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.blob();
}

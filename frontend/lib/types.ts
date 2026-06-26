export type StatusProgramacao = "OK" | "Atenção" | "Conflito" | "Já programado" | "Sem dados";

export type Colaborador = {
  id: string;
  codigo?: string | null;
  classe?: string | null;
  nome: string;
  dataAdmissao?: string | null;
  posto?: string | null;
  turno?: string | null;
  escala?: string | null;
  observacoes?: string | null;
};

export type PeriodoFerias = {
  id: string;
  colaboradorId: string;
  venctoFerias?: string | null;
  feriasVencidas?: string | null;
  feriasProporcionais?: string | null;
  inicioAquisitivo?: string | null;
  fimAquisitivo?: string | null;
  inicioGozoAtual?: string | null;
  fimGozoAtual?: string | null;
  diasDireito?: number | null;
  diasGozados?: number | null;
  diasRestantes?: number | null;
  limiteGozo?: string | null;
  diasAfastado?: number | null;
  diasFaltas?: number | null;
  abono?: string | null;
  decimoTerceiro?: string | null;
  original: Record<string, unknown>;
};

export type ProgramacaoSugerida = {
  id: string;
  periodoFeriasId: string;
  inicioSugerido?: string | null;
  fimSugerido?: string | null;
  diasProgramados?: number | null;
  status: StatusProgramacao;
  motivo: string;
  conflitos: string[];
};

export type ParametroOperacional = {
  posto: string;
  turno: string;
  escala: string;
  minimoAtivos: number;
  maximoFeriasSimultaneas: number;
  maximoGeralFeriasSimultaneas: number;
  colaboradoresIncompativeis: string[][];
  datasBloqueadas: string[];
  feristasDisponiveis: number;
  regraAbono: string;
  regraFracionamento: string;
  diasFeriasPadrao: number;
  antecedenciaMinimaDias: number;
};

export type ImportResult = {
  importacaoId: string;
  sheetName: string;
  availableSheets: string[];
  detectedColumns: Record<string, string>;
  rows: Record<string, unknown>[];
  preview: Record<string, unknown>[];
  errors: string[];
  colaboradores: Colaborador[];
  periodos: PeriodoFerias[];
  programacoes: ProgramacaoSugerida[];
};

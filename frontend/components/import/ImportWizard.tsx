"use client";

import { useMemo, useState } from "react";
import { uploadImportFile, type ImportUploadResponse, type WorksheetPreview } from "../../services/importApi";
import { Dropzone } from "./Dropzone";
import { PreviewTable } from "./PreviewTable";
import { UploadProgress } from "./UploadProgress";
import { WorksheetList } from "./WorksheetList";

export function ImportWizard() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ImportUploadResponse | null>(null);
  const [selectedWorksheet, setSelectedWorksheet] = useState<WorksheetPreview | null>(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [showWorksheetPicker, setShowWorksheetPicker] = useState(false);

  const activeWorksheet = useMemo(() => {
    return selectedWorksheet ?? result?.worksheets[0] ?? null;
  }, [result, selectedWorksheet]);

  const detection = result?.tableDetection;
  const lowConfidence = detection ? detection.confidence < 0.7 : false;
  const detectedRecords = detection ? Math.max(0, detection.lastRow - detection.dataStartRow + 1) : 0;
  const highlightedRow = detection && activeWorksheet?.sheetName === detection.worksheet ? detection.headerRow : undefined;

  async function handleUpload() {
    if (!file) return;

    setLoading(true);
    setProgress(0);
    setStatus("Enviando arquivo");
    setResult(null);
    setSelectedWorksheet(null);

    try {
      const uploadResult = await uploadImportFile(file, setProgress);
      setResult(uploadResult);
      setSelectedWorksheet(
        uploadResult.worksheets.find((worksheet) => worksheet.sheetName === uploadResult.tableDetection.worksheet) ??
          uploadResult.worksheets[0] ??
          null,
      );
      setShowWorksheetPicker(false);
      setStatus("Preview carregado");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Falha ao importar arquivo.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="grid two">
      <Dropzone disabled={loading} file={file} onFile={setFile} onUpload={handleUpload} />

      <div className="card stack">
        <h2>Status</h2>
        <UploadProgress progress={progress} status={status || "Aguardando arquivo"} />
        {result && (
          <>
            <p className="muted">
              Arquivo {result.fileName} carregado como {result.fileType.toUpperCase()}.
            </p>
            {detection && (
              <div className="detection-summary">
                <p>
                  <span aria-hidden="true">&#10003;</span> Aba detectada: <strong>{detection.worksheet || "Nao identificada"}</strong>
                </p>
                <p>
                  <span aria-hidden="true">&#10003;</span> Confianca: <strong>{Math.round(detection.confidence * 100)}%</strong>
                </p>
                <p>
                  <span aria-hidden="true">&#10003;</span> Linha do cabecalho: <strong>{detection.headerRow || "-"}</strong>
                </p>
                <p>
                  <span aria-hidden="true">&#10003;</span> Registros estimados: <strong>{detectedRecords}</strong>
                </p>
              </div>
            )}
            {lowConfidence && (
              <button className="secondary" onClick={() => setShowWorksheetPicker(true)} type="button">
                Selecionar outra aba
              </button>
            )}
            {!!result.errors.length && (
              <div className="errors">
                {result.errors.map((error) => (
                  <p key={error}>{error}</p>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      <div className="card stack">
        <h2>Abas encontradas</h2>
        {!result ? (
          <p className="muted">Envie uma planilha para listar as abas.</p>
        ) : showWorksheetPicker || lowConfidence ? (
          <WorksheetList
            onSelect={setSelectedWorksheet}
            selectedSheetName={activeWorksheet?.sheetName}
            worksheets={result.worksheets}
          />
        ) : (
          <p className="muted">A aba com maior pontuacao foi selecionada automaticamente.</p>
        )}
      </div>

      <div className="card stack">
        <h2>Previa das primeiras linhas</h2>
        {activeWorksheet && (
          <p className="muted">
            Aba {activeWorksheet.sheetName}: {activeWorksheet.columns.length} colunas, {activeWorksheet.rowCount} linhas.
          </p>
        )}
        <PreviewTable highlightedRowNumber={highlightedRow} rows={activeWorksheet?.preview ?? []} />
      </div>
    </section>
  );
}

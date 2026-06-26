"use client";

import type { ChangeEvent, DragEvent } from "react";
import { useState } from "react";

const ACCEPTED_EXTENSIONS = [".xls", ".xlsx", ".csv"];

type DropzoneProps = {
  file: File | null;
  disabled?: boolean;
  onFile: (file: File) => void;
  onUpload: () => void;
};

export function Dropzone({ file, disabled, onFile, onUpload }: DropzoneProps) {
  const [dragging, setDragging] = useState(false);

  function handleFile(candidate?: File) {
    if (!candidate) return;
    const isAccepted = ACCEPTED_EXTENSIONS.some((extension) => candidate.name.toLowerCase().endsWith(extension));
    if (isAccepted) {
      onFile(candidate);
    }
  }

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    handleFile(event.target.files?.[0]);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    handleFile(event.dataTransfer.files[0]);
  }

  return (
    <div
      className="card stack"
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      style={{ borderStyle: dragging ? "solid" : "dashed" }}
    >
      <h2>Upload de planilha</h2>
      <p className="muted">Arraste um arquivo XLS, XLSX ou CSV, ou selecione pelo computador.</p>
      <input accept=".xls,.xlsx,.csv" disabled={disabled} onChange={handleChange} type="file" />
      {file && <p>Arquivo selecionado: {file.name}</p>}
      <button disabled={!file || disabled} onClick={onUpload} type="button">
        Enviar e gerar previa
      </button>
    </div>
  );
}

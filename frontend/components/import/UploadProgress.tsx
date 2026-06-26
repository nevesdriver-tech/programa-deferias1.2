type UploadProgressProps = {
  progress: number;
  status?: string;
};

export function UploadProgress({ progress, status }: UploadProgressProps) {
  const boundedProgress = Math.max(0, Math.min(100, progress));

  return (
    <div className="stack">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <span>{status ?? "Enviando arquivo"}</span>
        <strong>{boundedProgress}%</strong>
      </div>
      <progress max={100} value={boundedProgress} style={{ width: "100%" }} />
    </div>
  );
}

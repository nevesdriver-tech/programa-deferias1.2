import type { WorksheetPreview } from "../../services/importApi";

type WorksheetListProps = {
  worksheets: WorksheetPreview[];
  selectedSheetName?: string;
  onSelect: (worksheet: WorksheetPreview) => void;
};

export function WorksheetList({ worksheets, selectedSheetName, onSelect }: WorksheetListProps) {
  if (!worksheets.length) {
    return <p className="muted">Nenhuma aba encontrada.</p>;
  }

  return (
    <div className="stack">
      {worksheets.map((worksheet) => (
        <button
          className={worksheet.sheetName === selectedSheetName ? "active" : "secondary"}
          key={worksheet.sheetName}
          onClick={() => onSelect(worksheet)}
          type="button"
        >
          {worksheet.sheetName} ({worksheet.rowCount} linhas)
        </button>
      ))}
    </div>
  );
}

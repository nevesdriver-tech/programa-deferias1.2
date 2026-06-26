type PreviewTableProps = {
  rows: Record<string, unknown>[];
};

export function PreviewTable({ rows }: PreviewTableProps) {
  if (!rows.length) {
    return <p className="muted">Nenhuma linha para exibir.</p>;
  }

  const headers = Object.keys(rows[0]);

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {headers.map((header) => (
              <th key={header}>{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {headers.map((header) => (
                <td key={header}>{String(row[header] ?? "")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

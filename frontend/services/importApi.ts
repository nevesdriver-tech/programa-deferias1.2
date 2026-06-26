const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type WorksheetPreview = {
  sheetName: string;
  rowCount: number;
  columns: string[];
  preview: Record<string, unknown>[];
};

export type ImportUploadResponse = {
  fileName: string;
  fileType: string;
  worksheets: WorksheetPreview[];
  errors: string[];
};

export function uploadImportFile(file: File, onProgress?: (progress: number) => void): Promise<ImportUploadResponse> {
  const form = new FormData();
  form.append("file", file);

  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open("POST", `${API_URL}/api/import/upload`);

    request.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        onProgress?.(Math.round((event.loaded / event.total) * 100));
      }
    };

    request.onload = () => {
      if (request.status >= 200 && request.status < 300) {
        onProgress?.(100);
        resolve(JSON.parse(request.responseText) as ImportUploadResponse);
        return;
      }

      reject(new Error(parseError(request.responseText) || `Erro ${request.status}`));
    };

    request.onerror = () => reject(new Error("Falha de rede ao enviar o arquivo."));
    request.send(form);
  });
}

function parseError(payload: string) {
  try {
    const parsed = JSON.parse(payload) as { detail?: string };
    return parsed.detail;
  } catch {
    return payload;
  }
}

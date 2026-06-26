# Programa de Ferias

Aplicacao web para importar planilhas de programacao de ferias, reconhecer cabecalhos quebrados em multiplas linhas e gerar uma previa automatica conforme regras de turno, escala, posto e cobertura.

## Stack

- Backend: FastAPI, SQLite, pandas, openpyxl, xlrd
- Frontend: Next.js, React, TypeScript
- Exportacao: Excel via backend e PDF em HTML imprimivel

## Como executar

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Por padrao o frontend usa `http://localhost:8000` como API. Ajuste `NEXT_PUBLIC_API_URL` se necessario.


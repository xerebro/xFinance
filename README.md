# xFinance

Agente financiero multi-compañía que integra SEC/EDGAR, Yahoo Finance y Azure OpenAI mediante LangGraph, expuesto vía FastAPI con frontend React estilo Perplexity.

## Requisitos

- Python 3.11+
- Node.js 18+

## Configuración del backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edita las credenciales de Azure OpenAI y el User-Agent de la SEC
uvicorn app.main:app --reload
```

## Configuración del frontend

```bash
cd web
npm install
npm run dev
```

## Flujo

1. El usuario consulta tickers/años/formas desde la UI.
2. FastAPI ejecuta el grafo LangGraph que coordina el MCP de la SEC y Yahoo Finance.
3. El frontend recibe streaming SSE y muestra el reporte con citas.
4. El reporte final puede descargarse como Markdown (`/api/report/<jobId>?format=markdown`).

## Nota

Este proyecto es informativo y no constituye asesoría financiera.

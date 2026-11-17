# RevSplit

RevSplit is a cashback and affiliate-arbitrage engine with a FastAPI backend,
React/Vite dashboard, Node.js webhook service, Redis cache, Kafka events, and
PostgreSQL ledger.

## Project structure

```text
RevSplit/
├── backend/
│   ├── app/
│   │   ├── core/              # settings, database, Redis, and Kafka
│   │   ├── routers/           # HTTP API routes
│   │   ├── services/          # business logic
│   │   ├── agents/            # LangGraph agent workflow
│   │   └── main.py            # FastAPI entry point
│   ├── requirements.txt
│   └── Dockerfile.fastapi
├── frontend/
│   └── src/                   # React dashboard
├── webhook_service/
│   └── src/                   # Node.js ingestion service
├── telegram_bot/
├── database/                  # PostgreSQL initialization SQL
├── notebooks/                 # Jupyter experiments
├── docker-compose.yml
└── package.json               # root development commands
```

## Prerequisites

- Docker Desktop (recommended), or Python 3.11 and Node.js 18+
- Copy `.env.example` to `.env` and set credentials for services you use.

## Recommended: run the complete stack with Docker

From the repository root in PowerShell:

```powershell
docker compose up -d --build
docker compose ps
```

Open:

- Frontend: http://localhost:5173 (run the frontend locally; Docker does not serve it)
- API health: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- Webhook service: http://localhost:3000
- Prometheus: http://localhost:9090

View logs and stop the stack:

```powershell
docker compose logs -f
docker compose down
```

## Run services locally

Start infrastructure first:

```powershell
docker compose up -d postgres redis zookeeper kafka
```

Install JavaScript dependencies:

```powershell
npm install
npm run install:all
```

Create and activate a Python environment, then install backend dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
```

Run the backend:

```powershell
npm run dev:backend
```

In separate PowerShell terminals, run the dashboard and optional Node.js
services:

```powershell
npm run dev:frontend
npm run dev:webhook
npm run dev:telegram
```

Or start all local application processes together:

```powershell
npm run dev
```

## Validate the project

```powershell
python -m compileall backend\app
npm --prefix frontend run build
```

The backend uses environment variables from `.env`; do not commit `.env` or
service credentials.

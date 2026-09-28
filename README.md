# RevSplit: Programmatic Cashback & AI Arbitrage Engine

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.11-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/AI%20Agents-LangGraph%20Multi--Agent-FF6F61.svg)](https://langchain-ai.github.io/langgraph/)
[![Supabase](https://img.shields.io/badge/Database-Supabase%20%7C%20PostgreSQL-3ECF8E.svg)](https://supabase.com/)
[![Redis](https://img.shields.io/badge/Cache-Redis%20(Token%20%26%20Locking)-DC382D.svg)](https://redis.io/)
[![Apache Kafka](https://img.shields.io/badge/Queue-Apache%20Kafka-231F20.svg)](https://kafka.apache.org/)

RevSplit is an enterprise-grade **Programmatic Cashback & Affiliate Arbitrage Engine** paired with an **Autonomous Multi-Agent AI System** (built on LangGraph and Google Gemini `gemini-3.6-flash`).

---

## 📂 Modular Architecture & Directory Structure

```
RevSplit/
├── frontend/                     # Interactive Glassmorphism Web App UI
│   ├── index.html                # Cashback Dashboard, Link Generator, Webhook & AI Inspector UI
│   ├── css/
│   │   └── style.css             # Glassmorphism Design System & Dark Mode
│   └── js/
│       └── app.js                # Async API Integration & Live Balance Updater
├── app/                          # Core Python FastAPI Backend & Multi-Agent Engine
│   ├── config.py                 # Pydantic Settings (Supabase, Postgres, Redis, Kafka)
│   ├── database.py               # Async SQLAlchemy / asyncpg Connection Pool
│   ├── redis_client.py           # Redis Token Caching & SETNX Lock Helper
│   ├── kafka_client.py           # Async Kafka Telemetry Producer
│   ├── main.py                   # FastAPI Application Entrypoint
│   ├── services/
│   │   ├── click_service.py      # Dynamic Sub ID Tokenization & Link Generator
│   │   └── ledger_service.py     # Row-Locking Settlement Engine (SELECT FOR UPDATE)
│   ├── routers/
│   │   ├── click_router.py       # Outbound Link Generation & HTTP 302 Gateway
│   │   └── webhook_router.py     # HMAC Verification & Ingestion Router
│   └── agents/
│       ├── state.py              # Typed AgentState Dictionary
│       ├── tools.py              # Custom @tool definitions for Agents A, B, C
│       ├── nodes.py              # Supervisor Orchestrator & Worker Nodes
│       ├── graph.py              # LangGraph Compiled StateGraph with Checkpointer
│       └── router.py             # FastAPI Multi-Agent Bridge Endpoint
├── webhook_service/              # Node.js High-Concurrency Ingestion Engine
│   ├── package.json              # Express, kafkajs, ioredis, @supabase/server
│   └── src/
│       ├── config.js
│       ├── hmac.js               # Cryptographic HMAC-SHA256 Signature Verifier
│       ├── consumer.js           # Kafka Settlement Worker with PostgreSQL Row Locks
│       └── index.js              # Express Ingestion Server
├── database/                     # SQL Migration Scripts for Local Postgres & Supabase
│   ├── 001_initial_schema.sql    # Local PostgreSQL DDL with Triggers & Functions
│   └── 002_supabase_schema.sql   # Supabase SQL Editor Script with RLS & Seed Data
├── docs/                         # System Architecture Documentation
│   ├── ARCHITECTURE.md           # High-Level Data Flow & Latency Specs
│   └── MULTI_AGENT_ARCHITECTURE.md # Multi-Agent Graph Architecture Specs
├── Agents/                       # AI Agent Notebooks & Performance Benchmarking
│   ├── agent_demo.ipynb          # Original LangChain & ReAct Agent Prototype
│   └── train_and_evaluate_agents.ipynb # LangGraph Agent Benchmark & Evaluation Notebook
├── docker-compose.yml            # Multi-Container Orchestration
└── README.md
```

---

## ⚡ Quick Start

### 1. Launch Backend Services
```bash
docker-compose up -d --build
```

### 2. Run AI Agent Evaluation & Benchmarking Notebook
Open [`Agents/train_and_evaluate_agents.ipynb`](file:///c:/Users/devra/OneDrive/Desktop/AI%20PROJECTS/Industry%20Level%20Projects/RevSplit/Agents/train_and_evaluate_agents.ipynb) in Jupyter Notebook / VS Code to evaluate agent latency, execution trace history, and risk scoring accuracy.

### 3. Open Frontend Dashboard UI
Open [`frontend/index.html`](file:///c:/Users/devra/OneDrive/Desktop/AI%20PROJECTS/Industry%20Level%20Projects/RevSplit/frontend/index.html) in your browser to interact with:
- Outbound Link Monetization Converter
- Real-Time Wallet Balance & Arbitrage Margin Monitor
- Live Merchant Webhook Simulator
- Autonomous Multi-Agent AI Inspection Panel

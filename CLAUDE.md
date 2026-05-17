# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**SAC AI** — Tool-Driven Conversational AI for customer support (SAC), with Multi-Agent architecture. Python 3.11+, FastAPI, OpenAI/Anthropic SDK, PostgreSQL, Redis, ChromaDB/pgvector.

## Commands

```bash
# Run dev server
uvicorn api.app:app --reload

# Run tests
pytest

# Run a single test file
pytest tests/unit/test_orchestrator.py

# Run a single test
pytest tests/unit/test_orchestrator.py::test_function_name

# Lint
ruff check .

# Format
ruff format .

# Seed knowledge base
python scripts/seed_knowledge.py

# Run DB migrations
python scripts/migrate_db.py

# Generate embeddings
python scripts/generate_embeddings.py

# Start all services
docker-compose up
```

## Architecture

8 independent layers communicating through well-defined interfaces:

| Layer | Location | Responsibility |
|-------|----------|----------------|
| Conversational | `modules/conversations/` + `api/routes/chat.py` | Manages user ↔ AI interaction, history, status |
| AI Orchestration | `modules/ai/orchestrator.py` + `ai/router.py` + `ai/agents/` | Intent detection, agent routing, response assembly |
| Tools | `modules/ai/tools/` | Controlled actions the AI can invoke |
| Domain | `modules/workflows/` + `modules/users/` | Business rules, validations, permissions |
| Integration | `modules/integrations/` | ERP, CRM, and external API clients |
| Knowledge | `modules/knowledge/` | FAQ, RAG, vector search, embeddings |
| Memory & Context | `memory/` | Session, history, preferences, context builder |
| Observability | `observability/` | Structured logs, metrics, tracing, audit |

## Request Flow

```
POST /chat → ConversationService → ContextBuilder → InputGuard
  → Orchestrator → LLM (classify intent) → IntentRouter
  → Agent → Tool(s) → Integration/Knowledge/Support
  → OutputGuard → ConversationService (save) → response
```

## Key Contracts

**`BaseAgent`** (`modules/ai/agents/base_agent.py`) — all agents must implement `name`, `description`, and `async handle(user_message, context) -> AgentResponse`. `AgentResponse` carries `message`, optional `tool_calls`, `escalate` flag, and `metadata`.

**`BaseTool`** (`modules/ai/tools/base_tool.py`) — all tools must implement `name`, `description`, `parameters_schema` (JSON Schema), and `async execute(**params) -> dict`.

**`IntentRouter`** (`modules/ai/router.py`) — maps intents (`faq`, `order_status`, `support`, `workflow`) to agent names. Default fallback is `faq_agent`.

**`Orchestrator`** (`modules/ai/orchestrator.py`) — receives `(user_message, session_id)`, runs the full pipeline via injected `llm_client`, `router`, `guardrails`, and `context_builder`.

## Extending the System

**New agent:** create in `modules/ai/agents/`, inherit `BaseAgent`, register intent mapping in `router.py`, add tools to `registry.py`, write tests in `tests/unit/test_agents.py`.

**New tool:** create in `modules/ai/tools/`, inherit `BaseTool`, register in `registry.py`.

**New integration:** create client in `modules/integrations/<system>/`, inherit `base_client.py` (provides retry, timeout, logging), expose via a tool in `modules/ai/tools/`.

## Configuration

All environment variables live in `config/settings.py` — never hardcoded. Copy `.env.example` to `.env` before running locally.

## User Roles

`modules/users/auth.py` enforces three roles: **user** (basic queries, FAQ, order status), **gestor** (reports, metrics, workflow approvals), **admin** (integrations config, knowledge base management, audit access).

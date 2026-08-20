# Soma Workspace Agent

> Personal Workspace Agent — an AI Agent system for learning management, exam prep, English learning, exercise tracking, game analysis, and job hunting.

[![CI](https://github.com/soma/soma-workspace-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/soma/soma-workspace-agent/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Overview

A multi-agent personal workspace built with **LangGraph + MCP Protocol + DeepSeek V4**, designed as a production-grade, enterprise-ready AI Agent system. The project follows a **Harness architecture** (inspired by OpenAI Codex CLI and DeepSeek's official design philosophy): the LLM is a stateless inference function, and the Harness layer manages state, tool execution, and orchestration.

### Six Functional Modules

| Module | Description |
|--------|-------------|
| **Learning Plan** | Track AI Agent learning progress, generate daily tasks, semantic note search |
| **Exam Prep** | Civil service exam study plan, question bank, mistake tracking, countdown |
| **English** | Vocabulary spaced repetition, scenario dialogue practice for travel |
| **Exercise** | Workout plans, records, statistics |
| **Game Assistant** | Dota 2 match replay analysis (OpenDota API), CS2 tournament tracking, extensible to new games |
| **Job Hunting** | JD collection & analysis, skill gap matrix, interview records & review |

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12+ |
| Backend | FastAPI + Pydantic v2 |
| Agent Orchestration | LangGraph (StateGraph + Supervisor pattern) |
| Tool Protocol | MCP (Model Context Protocol) |
| RAG | LlamaIndex + Qdrant (hybrid retrieval) |
| Database | PostgreSQL + Redis |
| LLM | DeepSeek V4 (flash + pro) |
| Observability | Langfuse |
| Frontend | Next.js + shadcn/ui + Recharts |
| Deployment | Docker Compose + GitHub Actions |

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker & Docker Compose (for PostgreSQL + Redis)
- DeepSeek API key ([get one here](https://platform.deepseek.com))

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/soma/soma-workspace-agent.git
cd soma-workspace-agent

# 2. Copy environment template and fill in your API key
cp .env.example .env
# Edit .env: set APP_DEEPSEEK_API_KEY=sk-your-key

# 3. Start PostgreSQL + Redis
docker compose up -d

# 4. Install Python dependencies
cd backend
uv sync --extra dev

# 5. Run tests
uv run pytest

# 6. Start the API server
uv run uvicorn app.main:app --reload
```

Visit `http://localhost:8000/health` to verify the server is running.

### Project Structure

```
soma-workspace-agent/
├── backend/
│   ├── app/           # FastAPI + LangGraph + RAG + agents
│   │   ├── main.py    # FastAPI entry point
│   │   ├── api/       # REST + SSE endpoints
│   │   ├── agents/    # LangGraph agent definitions
│   │   ├── core/      # Config, LLM factory, state, prompts
│   │   ├── mcp_servers/  # MCP Server implementations
│   │   └── ...
│   ├── tests/         # Unit, integration, eval tests
│   ├── pyproject.toml # Project config (uv + ruff + pytest + mypy)
│   └── Dockerfile
├── frontend/          # Next.js dashboard (W6+)
├── infra/             # Nginx, Langfuse, init scripts
├── docs/              # Design docs, API docs
├── docker-compose.yml # PostgreSQL + Redis
└── .github/workflows/ # CI/CD
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full system design.

## Development

```bash
# Lint
cd backend && uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run mypy app/

# Run tests with coverage
uv run pytest --cov=app
```

## License

MIT

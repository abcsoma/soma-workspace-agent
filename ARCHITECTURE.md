# Architecture Overview

> This document is a quick-reference summary. For the full engineering design, see `docs/工作台Agent详细设计文档.md`.

## Harness Architecture (Core Design Philosophy)

Inspired by OpenAI Codex CLI and DeepSeek's official Harness pattern:

```
┌──────────────────────────────────────────────────────────────────┐
│                    Harness Layer (stateful, we build)             │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  Session /   │  │  Tool Engine  │  │  Orchestration         │  │
│  │  State Mgmt  │  │  MCP Client   │  │  LangGraph Supervisor  │  │
│  │  Checkpoint  │  │  Schema Valid │  │  StateGraph            │  │
│  │  Memory      │  │               │  │                        │  │
│  └─────────────┘  └──────────────┘  └────────────────────────┘  │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  Scheduler   │  │  Security     │  │  Observability         │  │
│  │  APScheduler │  │  Guardrails   │  │  Langfuse Trace/Eval   │  │
│  └─────────────┘  └──────────────┘  └────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────────┘
                           │ stateless request: messages + tool_schemas
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│              DeepSeek V4 API (stateless inference function)       │
└──────────────────────────────────────────────────────────────────┘
```

**Key insight**: The model can be swapped (DeepSeek → Qwen → local vLLM) by changing `base_url` and `model` config. All stateful logic lives in the Harness.

## Five-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    UI Layer (Next.js)                        │
│  Learning │ Exam │ English │ Exercise │ Game │ Job          │
└─────┬──────────────────────────────────────────────────────┘
      │ SSE
┌─────▼──────────────────────────────────────────────────────┐
│              FastAPI Backend (Python)                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │          LangGraph Agent Orchestration                   ││
│  │  Router Agent → 6 sub-agents → Synthesizer              ││
│  │  Shared State + Checkpoint (PostgresSaver)              ││
│  └─────────────────────────────────────────────────────────┘│
└─────┬──────────────────────────────────────────────────────┘
      │
┌─────▼──────────────────────────────────────────────────────┐
│               MCP Server Layer                               │
│  Learning │ Exam │ English │ Exercise │ Game │ Job          │
│  (Each = independent process, StreamableHTTP transport)      │
└─────┬──────────────────────────────────────────────────────┘
      │
┌─────▼──────────────────────────────────────────────────────┐
│               Data & External Services                       │
│  PostgreSQL │ Qdrant │ Redis │ External APIs                 │
└─────────────────────────────────────────────────────────────┘
```

## Agent Orchestration (LangGraph Supervisor Pattern)

```
User Input
    │
    ▼
Router Agent (Supervisor)
    ├──→ Learning Agent  ──→ Learning MCP Server
    ├──→ Exam Agent       ──→ Exam MCP Server
    ├──→ English Agent    ──→ English MCP Server
    ├──→ Exercise Agent   ──→ Exercise MCP Server
    ├──→ Game Agent       ──→ Game MCP Server
    └──→ Job Agent        ──→ Job MCP Server
    │
    ▼
Synthesizer Agent ──→ Streamed Response
```

- **Parallel dispatch**: Multiple agents can run concurrently
- **Shared state**: `AgentState` (TypedDict) flows through StateGraph
- **Checkpoint**: PostgresSaver persists state for interrupt/resume
- **Human-in-the-Loop**: Plan confirmation via interrupt nodes

## MCP Server Layer

Each functional module is an independent MCP Server with standardized tool schemas. New modules are added by creating a new MCP Server and registering it in the Skills registry — no changes to the agent code.

```
Agent (MCP Client)
    ├── MCP Server: Learning (add_task, list_tasks, complete_task, search_notes)
    ├── MCP Server: Exam (get_questions, record_mistake, get_countdown)
    ├── MCP Server: English (add_word, review_words, practice_dialogue)
    ├── MCP Server: Exercise (log_workout, get_stats, get_plan)
    ├── MCP Server: Game (get_match, analyze_replay, get_hero_stats)
    └── MCP Server: Job (save_jd, analyze_jd, record_interview)
```

## RAG Pipeline

```
Ingest: Document → Semantic Chunk → Embedding → Qdrant (sparse + dense)
Query:  User Query → HyDE Rewrite → BM25 + Vector → Cross-encoder Rerank → Top-5 → LLM
Eval:   RAGAS (faithfulness, answer_relevancy, context_precision)
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Harness architecture** | Model is stateless; all state in our layer → swappable models |
| **MCP for all tools** | Industry standard protocol; plugin-like extensibility |
| **Skills hot-plug** | New module = new MCP Server + agent subgraph, no core changes |
| **Eval-driven development** | Prompt/model changes must pass golden dataset regression |
| **Capability > instruction limits** | Security via tool-layer authorization, not prompt pleading |

## Current Status

- [x] W1: Project skeleton + config + structured logging
- [ ] W2: Bare Agent Loop (DeepSeek + Function Calling)
- [ ] W3: Learning plan tools + CLI
- [ ] W4-6: LangGraph refactor + web UI
- [ ] W7-10: RAG + learning module complete
- [ ] W11-14: MCP servers + exam module
- [ ] W15-18: Multi-agent + English/exercise modules
- [ ] W19-22: Game + job modules
- [ ] W23-26: Production + frontend + open source

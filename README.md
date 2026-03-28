# AI Dev Team

An autonomous multi-agent AI coding system that simulates a software development team. A Leader Agent manages specialized AI agents that collaborate to design, write, test, debug, and deploy software from natural-language prompts.

## Architecture

```
User Interface
     ↓
API Gateway (FastAPI)
     ↓
Leader Agent (Project Manager)
     ↓
Task Planner
     ↓
Agent Dispatcher
     ↓
┌──────────────────────────────────────────┐
│  Research · Architect · Coder            │
│  Tester   · Debugger  · Documentation   │
└──────────────────────────────────────────┘
     ↓
Memory System (ChromaDB)
     ↓
Execution Environment (Sandbox)
     ↓
Final Output
```

## Core Agents

| Agent | Role | Responsibilities |
|-------|------|-----------------|
| **Leader** | Project Manager | Understand requests, plan, delegate, validate |
| **Research** | Researcher | Gather docs, search APIs, collect examples |
| **Architect** | System Designer | Design architecture, define modules, scaffold |
| **Coder** | Developer | Write production code, implement features |
| **Tester** | QA Engineer | Write tests, run validations |
| **Debugger** | Bug Fixer | Detect errors, analyse traces, fix bugs |
| **Documentation** | Tech Writer | Generate README, API docs, guides |

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
pip install -e ".[dev]"
```

### Run a Project (CLI)

```bash
ai-dev-team run "Build a REST API for a todo application"
```

### Start the API Server

```bash
ai-dev-team serve --reload
```

Then visit `http://localhost:8000/docs` for the interactive API docs.

### API Usage

```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Build a REST API for a todo application"}'
```

### Run Tests

```bash
pytest tests/ -v
```

## Project Structure

```
ai_dev_team/
├── agents/             # Specialised AI agents
│   ├── leader_agent.py
│   ├── coder_agent.py
│   ├── research_agent.py
│   ├── architect_agent.py
│   ├── tester_agent.py
│   ├── debug_agent.py
│   └── doc_agent.py
├── planner/
│   └── task_planner.py # Breaks requests into task graphs
├── memory/
│   ├── vector_memory.py    # ChromaDB vector store
│   └── memory_manager.py   # Short-term + long-term memory
├── tools/
│   ├── file_manager.py     # Sandboxed file operations
│   ├── web_search.py       # Web search integration
│   ├── code_executor.py    # Safe code execution sandbox
│   └── git_tool.py         # Git version control
├── core/
│   ├── agent_base.py              # Abstract base agent
│   ├── communication_protocol.py  # Inter-agent messaging
│   └── task_manager.py            # Task lifecycle management
├── api/
│   └── server.py       # FastAPI HTTP server
├── config/
│   └── settings.py      # Configuration management
└── main.py              # CLI entry point
```

## Configuration

Set environment variables to customise the system:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | LLM provider (openai, ollama, deepseek, anthropic) |
| `LLM_MODEL` | `gpt-4o` | Model name |
| `OPENAI_API_KEY` | — | API key for OpenAI |
| `LLM_BASE_URL` | — | Custom API base URL |
| `AI_DEV_TEAM_WORKSPACE` | `./workspace` | Project output directory |

## Tech Stack

- **Language**: Python 3.11+
- **API Framework**: FastAPI
- **Vector Database**: ChromaDB
- **LLM Integration**: LangChain + OpenAI
- **Testing**: pytest

## License

MIT

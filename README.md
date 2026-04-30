# Manufacturing Operations AI

Multi-agent **root cause analysis (RCA)** for manufacturing incidents. An LLM orchestrator picks specialist agents (quality, throughput, maintenance, supplier, safety); each agent uses domain tools and a shared **FAISS + RAG** knowledge base. A final **RCA synthesizer** merges findings into ranked hypotheses with confidence scores and recommended actions.

## Architecture

```text
Incident
    │
    ▼
Orchestrator (LLM selects agents)
    │
    ├── QualityAgent ───────┐
    ├── ThroughputAgent ────┤
    ├── MaintenanceAgent ───┼──► RCA Synthesizer ──► IncidentReport
    ├── SupplierAgent ─────┤       (ranked hypotheses + actions)
    └── SafetyAgent ───────┘
```

- **Graph:** [agents/graph.py](agents/graph.py) — LangGraph `StateGraph`, parallel fan-out, convergent RCA node.
- **RCA:** [agents/rca_agent.py](agents/rca_agent.py) — structured JSON report; resilient parsing for markdown-wrapped LLM output.
- **RAG:** [rag/knowledge_base.py](rag/knowledge_base.py) — FAISS index built from [data/seed_documents.py](data/seed_documents.py) (KBAs, standards, incidents, maintenance, supplier records).
- **Tools:** [tools/](tools/) — per-domain toolkits plus shared RAG helpers.
- **CLI:** [main.py](main.py) — Rich terminal output and three pre-wired demo scenarios.

## Requirements

- Python **3.10+** (tested with 3.11)
- API keys as described below

Install dependencies:

```bash
cd manufacturing_ai
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Create a **`.env`** file in the project root (do not commit it). Minimal variables:

| Variable | Purpose |
|----------|---------|
| `LLM_PROVIDER` | `anthropic` or `openai` |
| `ANTHROPIC_API_KEY` | Required if `LLM_PROVIDER=anthropic` |
| `OPENAI_API_KEY` | Required for **embeddings** (FAISS) always; required for chat if `LLM_PROVIDER=openai` |
| `ANTHROPIC_MODEL` | Optional; default `claude-sonnet-4-6` |
| `OPENAI_MODEL` | Optional; default `gpt-4o` |
| `EMBEDDING_MODEL` | Optional; default `text-embedding-3-small` |
| `VECTOR_STORE_PATH` | Optional; default `./vector_store` |
| `VERBOSE` | `true` / `false` |
| `MAX_AGENT_ITERATIONS` | Agent ReAct loop cap (default `6`) |
| `RAG_TOP_K` | Documents per retrieval (default `4`) |

**Note:** RAG uses **OpenAI embeddings** via `langchain_openai`. Set `OPENAI_API_KEY` even when the chat model is Anthropic.

## Usage

```bash
# Run one demo scenario (1, 2, or 3)
python main.py --scenario 1
python main.py --scenario 2
python main.py --scenario 3

# Run all three
python main.py

# Rebuild the FAISS index from seed documents (e.g. after editing documents or changing `EMBEDDING_MODEL`)
python main.py --rebuild-rag
```

### Demo scenarios

1. **Throughput drop on Line B** — routes to throughput, maintenance, quality (per orchestrator rules).
2. **Defect spike on Line B (welds)** — quality, maintenance, supplier.
3. **Missed supplier delivery** — supplier, throughput.

### Programmatic API

```python
from main import analyze_incident
from models.schemas import Incident

report = analyze_incident(
    Incident(
        id="INC-001",
        description="Output dropped on Line B...",
        plant_id="PLANT-A",
        line_id="LINE-B",
    )
)
```

## Project layout

```text
manufacturing_ai/
├── main.py                 # CLI + scenarios
├── config.py               # LLM, embeddings, env
├── models/schemas.py       # Incident, AgentFinding, IncidentReport, etc.
├── agents/
│   ├── graph.py            # LangGraph orchestration
│   ├── rca_agent.py        # RCA synthesizer
│   ├── base.py             # Shared agent / ReAct wiring
│   └── *_agent.py          # Domain agents
├── rag/knowledge_base.py   # FAISS build/load, retrievers
├── data/seed_documents.py  # Seed corpus for RAG
└── tools/                  # Domain + RAG tools
```

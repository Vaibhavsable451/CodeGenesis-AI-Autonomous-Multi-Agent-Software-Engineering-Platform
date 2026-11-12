# CodeGenesis AI – Autonomous Multi-Agent Software Engineering Platform

Ingests a GitHub repo or ZIP, maps the code, finds bugs and security issues with specialised
LLM agents (Groq, default model `openai/gpt-oss-120b`), generates tests, and validates them in an
isolated Docker sandbox. Nothing AI-generated is executed on the host or merged without approval.

## Quick start (Windows PowerShell)
```
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # then set GROQ_API_KEY
uvicorn backend.main:app --reload
streamlit run frontend/app.py     # in a second terminal
```
Sandbox image (needs Docker): `docker build -f infrastructure/sandbox.Dockerfile -t codegenesis-sandbox .`

Tests: `pytest -q` · Lint: `ruff check .`

## Status vs roadmap
| Phase | Status |
|---|---|
| 1 Foundation | Done |
| 2 Ingestion (URL, ZIP, file tree) | Done |
| 3 Code intelligence | Python AST, complexity, security heuristics done; Tree-sitter, call graph TODO |
| 4 DL/NLP | TODO (`ml/`) |
| 5 Code RAG (LlamaIndex + Pinecone) | TODO (`rag/`) |
| 6 Agents | Sequential pipeline in `agents/orchestrator.py`; migrate to LangGraph |
| 7 MCP | TODO (`mcp/`) |
| 8 Sandbox | `core/sandbox.py` done |
| 9–12 MLOps, UI polish, K8s, Azure | TODO |

## Model
Set in `.env`: `GROQ_MODEL=openai/gpt-oss-120b`. Change it there to switch models.

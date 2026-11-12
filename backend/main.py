from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from agents import orchestrator
from core import code_intel, ingestion
from core.config import settings
from core.logging import get_logger

log = get_logger("api")
app = FastAPI(title="CodeGenesis AI", version="0.1.0")


class GithubReq(BaseModel):
    url: str


class AnalyzeReq(BaseModel):
    repo_id: str
    instructions: str = ""


class ChatReq(BaseModel):
    repo_id: str
    question: str


@app.get("/health")
def health():
    return {"status": "ok", "model": settings.groq_model}


@app.post("/ingest/github")
def ingest_github(req: GithubReq):
    try:
        rid = ingestion.clone_github(req.url)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(502, str(e))
    return {"repo_id": rid, "files": ingestion.build_file_tree(rid)}


@app.post("/ingest/zip")
async def ingest_zip(file: UploadFile = File(...)):
    try:
        rid = ingestion.extract_zip(await file.read())
    except Exception as e:
        raise HTTPException(400, str(e))
    return {"repo_id": rid, "files": ingestion.build_file_tree(rid)}


@app.get("/repo/{repo_id}/tree")
def tree(repo_id: str):
    try:
        return {"files": ingestion.build_file_tree(repo_id)}
    except (ValueError, FileNotFoundError):
        raise HTTPException(404, "Repository not found")


@app.get("/repo/{repo_id}/intel")
def intel(repo_id: str):
    try:
        root = ingestion.repo_path(repo_id)
    except (ValueError, FileNotFoundError):
        raise HTTPException(404, "Repository not found")
    return code_intel.scan_repository(root, ingestion.build_file_tree(repo_id))


@app.post("/analyze")
def analyze(req: AnalyzeReq):
    try:
        root = ingestion.repo_path(req.repo_id)
        return orchestrator.run_pipeline(root, ingestion.build_file_tree(req.repo_id), req.instructions)
    except (ValueError, FileNotFoundError):
        raise HTTPException(404, "Repository not found")
    except RuntimeError as e:
        raise HTTPException(500, str(e))


@app.post("/chat")
def chat(req: ChatReq):
    try:
        root = ingestion.repo_path(req.repo_id)
        return {"answer": orchestrator.ask_code_question(root, ingestion.build_file_tree(req.repo_id), req.question)}
    except (ValueError, FileNotFoundError):
        raise HTTPException(404, "Repository not found")
    except RuntimeError as e:
        raise HTTPException(500, str(e))

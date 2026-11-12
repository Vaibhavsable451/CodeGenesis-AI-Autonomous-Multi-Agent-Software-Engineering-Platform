"""Multi-agent pipeline (Phase 6 will migrate this to LangGraph).
Each agent is a specialised prompt; the Reviewer verifies the others' output."""
import time

from core import llm
from core.logging import get_logger

log = get_logger("agents")

PAUSE_SECONDS = 25  # keeps usage under the free-tier 8,000 tokens/minute limit; set to 0 on a paid tier

AGENTS = {
    "bug_hunter": "You are a senior engineer hunting bugs. List concrete bugs with file path, line number, "
                  "why it is a bug, and a minimal fix. Only report issues you can justify from the code.",
    "security": "You are an application security expert. Identify vulnerabilities (OWASP, secrets, injection, "
                "unsafe deserialization) with file, line, severity and remediation.",
    "test_engineer": "You are a test engineer. Write pytest unit tests for the code given. Output a single "
                     "runnable Python test file in one ```python block. Do not use the network or the filesystem.",
    "reviewer": "You are a strict code reviewer. You are given another agent's findings and the source. "
                "Mark each finding CONFIRMED, UNCERTAIN or FALSE_POSITIVE with a one-line reason.",
}


def build_context(root, files: list[dict], max_chars: int = 6000) -> str:
    parts, used = [], 0
    for f in files:
        if not f["analyzable"]:
            continue
        text = (root / f["path"]).read_text(errors="ignore")
        numbered = "\n".join(f"{i}: {line}" for i, line in enumerate(text.splitlines(), 1))
        chunk = f"### FILE: {f['path']}\n{numbered}\n"
        if used + len(chunk) > max_chars:
            break
        parts.append(chunk)
        used += len(chunk)
    return "\n".join(parts)


def run_pipeline(root, files: list[dict], instructions: str = "") -> dict:
    context = build_context(root, files)
    if not context:
        return {"error": "No analyzable source files found (or the first file is too large)"}
    task = f"{instructions}\n\n{context}" if instructions else context
    results = {}
    for name in ("bug_hunter", "security", "test_engineer"):
        log.info("Running agent: %s", name)
        results[name] = llm.chat(AGENTS[name], task)
        time.sleep(PAUSE_SECONDS)
    log.info("Running agent: reviewer")
    verification = (f"SOURCE:\n{context}\n\nBUG FINDINGS:\n{results['bug_hunter']}"
                    f"\n\nSECURITY FINDINGS:\n{results['security']}")
    results["reviewer"] = llm.chat(AGENTS["reviewer"], verification)
    return results


def ask_code_question(root, files: list[dict], question: str) -> str:
    context = build_context(root, files)
    return llm.chat("Answer questions about this codebase. Cite file paths and line numbers.",
                    f"{context}\n\nQUESTION: {question}")
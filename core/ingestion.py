"""Repository ingestion: GitHub URL validation, clone, ZIP upload, file tree."""
import io
import re
import shutil
import subprocess
import uuid
import zipfile
from pathlib import Path

from core.config import settings
from core.logging import get_logger

log = get_logger("ingestion")

GITHUB_RE = re.compile(r"^https://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?$")
LANGS = {".py": "python", ".java": "java", ".js": "javascript", ".ts": "typescript",
         ".jsx": "javascript", ".tsx": "typescript"}
EXCLUDE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build",
                ".idea", ".vscode", "target", ".next"}


def validate_github_url(url: str) -> tuple[str, str]:
    m = GITHUB_RE.match(url.strip())
    if not m:
        raise ValueError("Invalid GitHub URL. Expected https://github.com/<owner>/<repo>")
    return m.group(1), m.group(2)


def _new_repo_dir() -> tuple[str, Path]:
    rid = uuid.uuid4().hex[:12]
    path = settings.data_dir / "repos" / rid
    path.mkdir(parents=True, exist_ok=True)
    return rid, path


def clone_github(url: str) -> str:
    owner, repo = validate_github_url(url)
    rid, path = _new_repo_dir()
    target = path / repo
    clone_url = f"https://github.com/{owner}/{repo}.git"
    try:
        subprocess.run(["git", "clone", "--depth", "1", clone_url, str(target)],
                       check=True, capture_output=True, timeout=120)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        shutil.rmtree(path, ignore_errors=True)
        raise RuntimeError(f"Clone failed (is the repo public?): {e}") from e
    shutil.rmtree(target / ".git", ignore_errors=True)
    return rid


def extract_zip(data: bytes) -> str:
    if len(data) > settings.max_zip_mb * 1024 * 1024:
        raise ValueError(f"ZIP larger than {settings.max_zip_mb} MB")
    rid, path = _new_repo_dir()
    root = path.resolve()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for member in zf.infolist():
            dest = (root / member.filename).resolve()
            if root not in dest.parents and dest != root:  # zip-slip protection
                raise ValueError(f"Unsafe path in ZIP: {member.filename}")
        zf.extractall(root)
    return rid


def repo_path(repo_id: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{12}", repo_id):
        raise ValueError("Invalid repo id")
    p = settings.data_dir / "repos" / repo_id
    if not p.exists():
        raise FileNotFoundError(repo_id)
    return p


def build_file_tree(repo_id: str) -> list[dict]:
    root = repo_path(repo_id)
    files = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or any(part in EXCLUDE_DIRS for part in p.relative_to(root).parts):
            continue
        size = p.stat().st_size
        files.append({
            "path": p.relative_to(root).as_posix(),
            "language": LANGS.get(p.suffix.lower(), "other"),
            "size": size,
            "analyzable": p.suffix.lower() in LANGS and size <= settings.max_file_kb * 1024,
        })
    return files

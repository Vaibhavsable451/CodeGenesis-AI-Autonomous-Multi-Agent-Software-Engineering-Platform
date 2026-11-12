"""Docker sandbox: AI-generated code NEVER runs on the host."""
import subprocess
import tempfile
from pathlib import Path

IMAGE = "codegenesis-sandbox"


def run_pytest(source_dir: Path, extra_files: dict[str, str] | None = None,
               timeout: int = 60) -> dict:
    """Run pytest in an isolated container: no network, CPU/mem/pid limits,
    read-only source mount, read-only root filesystem."""
    with tempfile.TemporaryDirectory() as tmp:
        for name, content in (extra_files or {}).items():
            target = (Path(tmp) / name).resolve()
            if Path(tmp).resolve() not in target.parents:
                raise ValueError(f"Unsafe path: {name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", "512m", "--cpus", "1", "--pids-limit", "128",
            "--read-only", "--tmpfs", "/tmp:rw,size=64m",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "-v", f"{source_dir.resolve()}:/work/src:ro",
            "-v", f"{tmp}:/work/generated:ro",
            "-w", "/work", "-e", "PYTHONDONTWRITEBYTECODE=1",
            "-e", "PYTHONPATH=/work/src",
            IMAGE, "python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "/work/generated",
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return {"exit_code": r.returncode, "stdout": r.stdout[-8000:], "stderr": r.stderr[-4000:]}
        except subprocess.TimeoutExpired:
            return {"exit_code": -1, "stdout": "", "stderr": f"Timed out after {timeout}s"}
        except FileNotFoundError:
            return {"exit_code": -2, "stdout": "", "stderr": "Docker is not installed or not running"}

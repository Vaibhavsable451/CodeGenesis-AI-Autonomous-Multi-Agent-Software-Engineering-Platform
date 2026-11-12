import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    reasoning_effort: str = os.getenv("GROQ_REASONING_EFFORT", "medium")
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    data_dir: Path = Path(os.getenv("DATA_DIR", "data"))
    max_zip_mb: int = 50
    max_file_kb: int = 512


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)

"""Groq LLM client. Default model: openai/gpt-oss-120b."""
import time

import groq
from groq import Groq

from core.config import settings
from core.logging import get_logger

log = get_logger("llm")
_client = None


def _get_client() -> Groq:
    global _client
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Copy .env.example to .env and fill it in.")
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def chat(system: str, user: str, temperature: float = 0.2, max_tokens: int = 1500) -> str:
    for attempt in range(4):
        try:
            resp = _get_client().chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                max_completion_tokens=max_tokens,
                reasoning_effort="low",  # reasoning tokens also count toward the TPM limit
            )
            return resp.choices[0].message.content or ""
        except groq.RateLimitError:
            log.warning("Rate limited, waiting 30s (attempt %d/4)", attempt + 1)
            time.sleep(30)
        except groq.APIStatusError as e:
            raise RuntimeError(f"Groq API error {e.status_code}: {e.message}") from e
        except groq.APIConnectionError as e:
            raise RuntimeError(f"Cannot reach Groq: {e}") from e
    raise RuntimeError("Groq rate limit still exceeded. Wait a minute or reduce the code size.")
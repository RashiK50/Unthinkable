"""The only module that imports the Gemini SDK. Swapping models/providers
touches this file and config — nothing else."""
import asyncio
import re
from typing import Any, TypeVar

import structlog
from google import genai
from google.genai import types as genai_types
from google.genai.errors import ClientError
from pydantic import BaseModel, ValidationError

from app.core.config import get_settings

logger = structlog.get_logger()

T = TypeVar("T", bound=BaseModel)

_client: genai.Client | None = None

# Free-tier Gemini allows ~5 requests/min. The pipeline fires cleaning + 5 extractors
# + summary in a burst, so 429s are expected — retry honoring the server's retryDelay
# instead of hard-failing the agent.
_RATE_LIMIT_RETRIES = 4
_DEFAULT_BACKOFF_SECONDS = 30.0


def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=get_settings().gemini_api_key)
    return _client


def _retry_delay_seconds(exc: ClientError) -> float:
    """Pull the server-advised retry delay out of a 429, else fall back."""
    match = re.search(r"retryDelay['\":\s]+(\d+(?:\.\d+)?)s", str(exc))
    if match:
        return min(float(match.group(1)) + 1.0, 65.0)
    return _DEFAULT_BACKOFF_SECONDS


async def _generate_with_backoff(**kwargs: Any) -> Any:
    """generate_content wrapper that retries on 429 RESOURCE_EXHAUSTED."""
    client = get_client()
    for attempt in range(_RATE_LIMIT_RETRIES + 1):
        try:
            return await client.aio.models.generate_content(**kwargs)
        except ClientError as exc:
            if exc.code != 429 or attempt == _RATE_LIMIT_RETRIES:
                raise
            delay = _retry_delay_seconds(exc)
            logger.warning("gemini_rate_limited", attempt=attempt, sleeping=delay)
            await asyncio.sleep(delay)
    raise RuntimeError("unreachable")


async def generate_structured(
    prompt: str,
    schema: type[T],
    model: str | None = None,
    temperature: float = 0.2,
    retries: int = 2,
) -> T:
    """Structured generation with bounded validation-feedback retries."""
    settings = get_settings()
    model = model or settings.gemini_agent_model
    client = get_client()
    attempt_prompt = prompt
    last_error: Exception | None = None

    for attempt in range(retries + 1):
        resp = await _generate_with_backoff(
            model=model,
            contents=attempt_prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=temperature,
            ),
        )
        try:
            return schema.model_validate_json(resp.text or "")
        except ValidationError as exc:
            last_error = exc
            logger.warning("structured_output_invalid", model=model, attempt=attempt)
            attempt_prompt = (
                f"{prompt}\n\nYour previous response failed validation with:\n{exc}\n"
                "Return ONLY valid JSON matching the schema."
            )
    raise RuntimeError(f"Structured generation failed after {retries + 1} attempts: {last_error}")


async def generate_text(prompt: str, model: str | None = None, temperature: float = 0.4) -> str:
    settings = get_settings()
    resp = await _generate_with_backoff(
        model=model or settings.gemini_agent_model,
        contents=prompt,
        config=genai_types.GenerateContentConfig(temperature=temperature),
    )
    return (resp.text or "").strip()


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch embeddings. output_dimensionality is pinned to the DB column width so
    models that default to a wider vector (e.g. gemini-embedding-001 → 3072) are
    truncated to fit `transcript_chunks.embedding vector(N)`."""
    settings = get_settings()
    client = get_client()
    out: list[list[float]] = []
    for i in range(0, len(texts), 100):
        batch = texts[i : i + 100]
        resp = await client.aio.models.embed_content(
            model=settings.gemini_embedding_model,
            contents=batch,
            config=genai_types.EmbedContentConfig(
                output_dimensionality=settings.embedding_dimensions
            ),
        )
        out.extend([list(e.values) for e in resp.embeddings])
    return out

"""The only module that imports the Gemini SDK. Swapping models/providers
touches this file and config — nothing else."""
from typing import TypeVar

import structlog
from google import genai
from google.genai import types as genai_types
from pydantic import BaseModel, ValidationError

from app.core.config import get_settings

logger = structlog.get_logger()

T = TypeVar("T", bound=BaseModel)

_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=get_settings().gemini_api_key)
    return _client


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
        resp = await client.aio.models.generate_content(
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
    client = get_client()
    resp = await client.aio.models.generate_content(
        model=model or settings.gemini_agent_model,
        contents=prompt,
        config=genai_types.GenerateContentConfig(temperature=temperature),
    )
    return (resp.text or "").strip()


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch embeddings (Gemini caps batch size; 100 is comfortably under it)."""
    settings = get_settings()
    client = get_client()
    out: list[list[float]] = []
    for i in range(0, len(texts), 100):
        batch = texts[i : i + 100]
        resp = await client.aio.models.embed_content(
            model=settings.gemini_embedding_model, contents=batch
        )
        out.extend([list(e.values) for e in resp.embeddings])
    return out

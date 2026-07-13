"""Typed application configuration. The app refuses to boot half-configured."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "MeetIQ API"
    environment: str = "development"
    frontend_origin: str = "http://localhost:5173"

    database_url: str

    supabase_url: str
    supabase_service_role_key: str
    supabase_jwt_secret: str
    storage_bucket: str = "meeting-audio"
    signed_url_ttl_seconds: int = 3600

    gemini_api_key: str
    gemini_agent_model: str = "gemini-2.5-flash"
    gemini_summary_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "text-embedding-004"
    embedding_dimensions: int = 768

    transcription_provider: str = "deepgram"  # deepgram | whisper
    deepgram_api_key: str = ""
    openai_api_key: str = ""

    max_upload_bytes: int = 500 * 1024 * 1024
    allowed_audio_extensions: frozenset[str] = frozenset({"mp3", "wav", "mp4", "m4a"})
    max_prompt_chars: int = 120_000
    rag_top_k: int = 6

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

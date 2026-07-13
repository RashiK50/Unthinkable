"""Thin async client for Supabase Storage. Audio bytes never pass through our API —
we only mint signed URLs (upload for the browser, download for the transcriber)."""
import httpx

from app.core.config import Settings
from app.core.exceptions import AppError


class StorageClient:
    def __init__(self, settings: Settings) -> None:
        self._base = f"{settings.supabase_url}/storage/v1"
        self._bucket = settings.storage_bucket
        self._ttl = settings.signed_url_ttl_seconds
        self._headers = {
            "apikey": settings.supabase_service_role_key,
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
        }

    async def create_signed_upload_url(self, path: str) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self._base}/object/upload/sign/{self._bucket}/{path}",
                headers=self._headers,
            )
        if resp.status_code >= 400:
            raise AppError(f"Storage signed-upload failed: {resp.text}")
        return f"{self._base}{resp.json()['url']}"

    async def create_signed_download_url(self, path: str) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self._base}/object/sign/{self._bucket}/{path}",
                headers=self._headers,
                json={"expiresIn": self._ttl},
            )
        if resp.status_code >= 400:
            raise AppError(f"Storage signed-download failed: {resp.text}")
        return f"{self._base}{resp.json()['signedURL']}"

    async def delete_object(self, path: str) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.delete(
                f"{self._base}/object/{self._bucket}/{path}", headers=self._headers
            )
        # 404 is fine — deleting a meeting whose upload never finished.
        if resp.status_code >= 400 and resp.status_code != 404:
            raise AppError(f"Storage delete failed: {resp.text}")

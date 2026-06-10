"""
Cliente HTTP hacia el backend FastAPI.
Maneja: login automático, refresh de token, reintentos con backoff.
"""
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx
from tenacity import (
    retry, stop_after_attempt, wait_exponential,
    retry_if_exception_type, before_sleep_log,
)

from agent.config import settings
from utils.logger import get_logger

log = get_logger("api_client")


class TokenStore:
    def __init__(self):
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.expires_at: datetime | None = None

    def is_expired(self) -> bool:
        if not self.expires_at:
            return True
        # Renueva 60 segundos antes de expirar
        return datetime.now(timezone.utc) >= self.expires_at - timedelta(seconds=60)

    def store(self, data: dict) -> None:
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        expires_in = data.get("expires_in", 3600)
        self.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)


class APIClient:
    def __init__(self):
        self._token = TokenStore()
        self._client: httpx.AsyncClient | None = None
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=settings.API_BASE_URL,
            timeout=httpx.Timeout(10.0, connect=5.0),
            http2=True,
        )
        await self._ensure_token()
        return self

    async def __aexit__(self, *_):
        if self._client:
            await self._client.aclose()

    # ── Auth ──────────────────────────────────────────────────────────────────
    async def _login(self) -> None:
        log.info("api.login", email=settings.API_EMAIL)
        resp = await self._client.post(
            "/auth/login",
            json={
                "email": settings.API_EMAIL,
                "password": settings.API_PASSWORD,
                "tenant_slug": settings.TENANT_SLUG,
            },
        )
        resp.raise_for_status()
        self._token.store(resp.json())
        log.info("api.login.ok")

    async def _refresh(self) -> None:
        log.info("api.token_refresh")
        try:
            resp = await self._client.post(
                "/auth/refresh",
                json={"refresh_token": self._token.refresh_token},
            )
            resp.raise_for_status()
            self._token.store(resp.json())
            log.info("api.token_refresh.ok")
        except httpx.HTTPStatusError:
            log.warning("api.token_refresh.failed — re-login")
            await self._login()

    async def _ensure_token(self) -> None:
        async with self._lock:
            if not self._token.access_token:
                await self._login()
            elif self._token.is_expired():
                await self._refresh()

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token.access_token}"}

    # ── Request con retry ─────────────────────────────────────────────────────
    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
        stop=stop_after_attempt(settings.API_RETRY_ATTEMPTS),
        wait=wait_exponential(
            multiplier=settings.API_RETRY_WAIT_SECONDS, min=1, max=30
        ),
    )
    async def _request(self, method: str, path: str, **kwargs) -> dict:
        await self._ensure_token()
        resp = await self._client.request(
            method, path, headers=self._auth_headers(), **kwargs
        )
        if resp.status_code == 401:
            # Token inválido — forzar re-login
            self._token.access_token = None
            await self._ensure_token()
            resp = await self._client.request(
                method, path, headers=self._auth_headers(), **kwargs
            )
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    # ── Métodos de dominio ────────────────────────────────────────────────────
    async def ingest_event(self, payload: dict) -> dict:
        """Envía una detección al backend."""
        return await self._request("POST", "/events/ingest", json=payload)

    async def get_presign_upload_url(
        self, camera_id: str, filename: str
    ) -> tuple[str, str]:
        """Retorna (upload_url, s3_key) para subir directo a MinIO."""
        data = await self._request(
            "GET",
            f"/cameras/{camera_id}/presign-upload",
            params={"filename": filename},
        )
        return data["upload_url"], data["s3_key"]

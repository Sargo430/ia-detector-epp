"""
Redis → WebSocket Bridge
-------------------------
Escucha el canal Redis `alerts:{tenant_id}` (el mismo que usa el backend
para publicar alertas desde los eventos de los agentes edge) y retransmite
cada mensaje a todos los clientes WebSocket del tenant correspondiente.

El suscriptor corre como una tarea asyncio de larga duración, iniciada en
el lifespan de FastAPI.

Canal Redis esperado:
    PUBLISH alerts:acme-corp  '{"event_type":"intrusion", ...}'

La función `publish_alert` se puede importar desde cualquier módulo del
backend (ej. el endpoint POST /events) para publicar en Redis.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncIterator

import redis.asyncio as aioredis

from app.core.config   import settings
from app.websockets.manager import manager

logger = logging.getLogger(__name__)

CHANNEL_PATTERN = "alerts:*"   # glob — suscribe a todos los tenants a la vez


# ── Publisher (usado por el resto del backend) ────────────────────────────────

async def publish_alert(redis: aioredis.Redis, tenant_id: str, payload: dict) -> None:
    """
    Publica una alerta en el canal Redis del tenant.

    Llamar desde el endpoint POST /api/v1/events (o el worker Celery)
    después de persistir el evento en la BD.

    Ejemplo:
        await publish_alert(redis, tenant_id="acme-corp", payload={
            "event_type":  "intrusion",
            "camera_id":   "cam-03",
            "camera_name": "Pasillo Central",
            "zone":        "Zona A",
            "severity":    "critical",
            "confidence":  94,
            "ts":          "2025-03-12T14:32:00Z",
        })
    """
    channel = f"alerts:{tenant_id}"
    await redis.publish(channel, json.dumps(payload))
    logger.debug("Published to %s: %s", channel, payload.get("event_type"))


# ── Subscriber task ───────────────────────────────────────────────────────────

async def alert_subscriber(redis_url: str | None = None) -> None:
    """
    Tarea asyncio de larga duración.
    Reconecta automáticamente si se pierde la conexión con Redis.
    Iniciar desde el lifespan de FastAPI:

        asyncio.create_task(alert_subscriber())
    """
    url = redis_url or settings.REDIS_URL
    retry_delay = 1.0

    while True:
        try:
            async with aioredis.from_url(url, decode_responses=True) as redis:
                pubsub = redis.pubsub()
                await pubsub.psubscribe(CHANNEL_PATTERN)
                logger.info("Redis pubsub subscribed to pattern: %s", CHANNEL_PATTERN)
                retry_delay = 1.0  # reset on successful connect

                async for raw in _iter_messages(pubsub):
                    await _dispatch(raw)

        except asyncio.CancelledError:
            logger.info("alert_subscriber cancelled — shutting down")
            return
        except Exception as exc:
            logger.warning("Redis pubsub error: %s — retrying in %.1fs", exc, retry_delay)
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)


async def _iter_messages(pubsub) -> AsyncIterator[dict]:
    """Yield sólo los mensajes de tipo 'pmessage' (datos reales)."""
    async for message in pubsub.listen():
        if message["type"] == "pmessage":
            yield message


async def _dispatch(raw: dict) -> None:
    """
    Extrae el tenant_id del canal y retransmite el payload a los clientes WS.

    Canal formato: alerts:<tenant_id>
    """
    channel: str = raw.get("channel", "")
    data:    str = raw.get("data", "{}")

    # Extraer tenant_id del nombre del canal
    parts = channel.split(":", 1)
    if len(parts) != 2:
        logger.warning("Unexpected channel format: %s", channel)
        return

    tenant_id = parts[1]

    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        logger.warning("Invalid JSON on channel %s: %s", channel, data)
        return

    active = manager.active_connections(tenant_id)
    if active:
        logger.debug("Dispatching to %d clients in tenant=%s", active, tenant_id)
        await manager.broadcast_to_tenant(tenant_id, payload)

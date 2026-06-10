"""
WebSocket Connection Manager
-----------------------------
Gestiona conexiones WebSocket activas agrupadas por tenant_id.
Thread-safe para uso con asyncio (FastAPI).

Uso típico:
    manager = ConnectionManager()

    # En el endpoint WS
    await manager.connect(websocket, tenant_id="acme", user_id="usr-1")

    # Desde el publisher Redis
    await manager.broadcast_to_tenant(tenant_id="acme", payload={...})
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class ConnectedClient:
    websocket: WebSocket
    user_id:   str
    tenant_id: str


class ConnectionManager:
    def __init__(self) -> None:
        # tenant_id → set of ConnectedClient
        self._rooms: Dict[str, Set[ConnectedClient]] = defaultdict(set)
        self._lock  = asyncio.Lock()

    # ── Public API ────────────────────────────────────────────────────────────

    async def connect(self, websocket: WebSocket, tenant_id: str, user_id: str) -> ConnectedClient:
        """Acepta la conexión WS y la registra en el room del tenant."""
        await websocket.accept()
        client = ConnectedClient(websocket=websocket, tenant_id=tenant_id, user_id=user_id)
        async with self._lock:
            self._rooms[tenant_id].add(client)
        logger.info("WS connected  user=%s tenant=%s  total_in_room=%d",
                    user_id, tenant_id, len(self._rooms[tenant_id]))
        return client

    async def disconnect(self, client: ConnectedClient) -> None:
        """Elimina el cliente del room. Idempotente."""
        async with self._lock:
            self._rooms[client.tenant_id].discard(client)
            if not self._rooms[client.tenant_id]:
                del self._rooms[client.tenant_id]
        logger.info("WS disconnected user=%s tenant=%s", client.user_id, client.tenant_id)

    async def broadcast_to_tenant(self, tenant_id: str, payload: dict) -> None:
        """
        Envía `payload` (como JSON) a todos los clientes del tenant.
        Las conexiones muertas se descartan silenciosamente.
        """
        async with self._lock:
            clients = set(self._rooms.get(tenant_id, set()))   # snapshot

        if not clients:
            return

        dead: list[ConnectedClient] = []
        for client in clients:
            try:
                await client.websocket.send_json(payload)
            except Exception:
                dead.append(client)

        for client in dead:
            await self.disconnect(client)

    def active_connections(self, tenant_id: str | None = None) -> int:
        """Devuelve el número de conexiones activas, opcionalmente filtradas por tenant."""
        if tenant_id:
            return len(self._rooms.get(tenant_id, set()))
        return sum(len(v) for v in self._rooms.values())


# Singleton — importar este objeto en los endpoints y el publisher
manager = ConnectionManager()

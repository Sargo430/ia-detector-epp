"""
WebSocket endpoint — /ws/alerts
---------------------------------
Acepta conexiones WebSocket autenticadas con JWT. Soporta dos métodos de
autenticación para cubrir distintos entornos de cliente:

  1. Query param:  ws://host/ws/alerts?token=<jwt>
     → Compatible con todos los clientes WebSocket, incluido el browser nativo.

  2. Header Sec-WebSocket-Protocol: <jwt>
     → Compatible con clientes que no pueden pasar query params (ej. algunos
       proxies o librerías nativas iOS/Android).
     → El servidor responde con el mismo subprotocolo para completar el handshake.

Flujo:
    Cliente →  WS connect  →  validar JWT  →  registrar en ConnectionManager
           ←  {"type": "connected", ...}   ←
           ←  {"type": "alert", ...}       ← (cuando llega un evento Redis)
           →  {"type": "ping"}             →  (keepalive opcional)
           ←  {"type": "pong"}             ←

Cierre limpio:
    El servidor espera mensajes del cliente en un loop. Si el cliente cierra
    la conexión (WebSocketDisconnect) o el token expira, se desconecta y se
    elimina del manager.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi             import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from jose                import JWTError, jwt

from app.core.config     import settings
from app.core.security   import ALGORITHM          # "HS256"
from app.websockets.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()

# ── JWT helpers ───────────────────────────────────────────────────────────────

def _decode_token(token: str) -> dict:
    """
    Decodifica y valida el JWT.
    Lanza ValueError con un mensaje legible si el token es inválido o expirado.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc

    # Verificar expiración manualmente para dar un mensaje claro
    exp = payload.get("exp")
    if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(tz=timezone.utc):
        raise ValueError("Token expired")

    return payload


def _extract_token(
    websocket: WebSocket,
    token_param: str | None,
) -> str:
    """
    Devuelve el JWT del query param o del header Sec-WebSocket-Protocol.
    Lanza ValueError si no se encuentra ninguno.
    """
    if token_param:
        return token_param

    # Sec-WebSocket-Protocol puede contener el token como único subprotocolo
    protocol_header = websocket.headers.get("sec-websocket-protocol", "")
    if protocol_header:
        # Algunos clientes envían "Bearer <token>" o directamente el token
        token = protocol_header.strip().removeprefix("Bearer").strip()
        if token:
            return token

    raise ValueError("No authentication token provided")


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.websocket("/ws/alerts")
async def ws_alerts(
    websocket:   WebSocket,
    token:       str | None = Query(default=None, description="JWT de autenticación"),
):
    """
    Endpoint WebSocket de alertas en tiempo real.

    Autenticación:
      - Query param:  ?token=<jwt>
      - Header:       Sec-WebSocket-Protocol: <jwt>

    El cliente recibe eventos del tenant al que pertenece el usuario
    autenticado. No se mezclan datos entre tenants (schema-per-tenant).
    """
    # ── 1. Extraer y validar JWT ANTES de aceptar la conexión ────────────────
    try:
        raw_token = _extract_token(websocket, token)
        claims    = _decode_token(raw_token)
    except ValueError as exc:
        # Rechazar sin aceptar — código 4001 (dominio de app)
        await websocket.close(code=4001, reason=str(exc))
        logger.warning("WS auth rejected: %s  ip=%s", exc, websocket.client.host)
        return

    tenant_id: str = claims.get("tenant_id", "")
    user_id:   str = claims.get("sub", "unknown")

    if not tenant_id:
        await websocket.close(code=4002, reason="Token missing tenant_id claim")
        return

    # ── 2. Responder subprotocolo si el cliente lo envió ────────────────────
    #     Necesario para que el handshake WS sea válido cuando se usa el header.
    protocol_header = websocket.headers.get("sec-websocket-protocol", "")
    subprotocols    = [p.strip() for p in protocol_header.split(",") if p.strip()]

    # ── 3. Registrar en el manager ───────────────────────────────────────────
    client = await manager.connect(websocket, tenant_id=tenant_id, user_id=user_id)

    # ── 4. Enviar mensaje de bienvenida ──────────────────────────────────────
    try:
        await websocket.send_json({
            "type":      "connected",
            "tenant_id": tenant_id,
            "user_id":   user_id,
            "message":   "Vigilance alert stream ready",
        })
    except Exception:
        await manager.disconnect(client)
        return

    # ── 5. Loop de recepción (keepalive + cierre limpio) ─────────────────────
    try:
        while True:
            # Esperar mensajes del cliente con timeout (detecta conexiones muertas)
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=60.0)
            except asyncio.TimeoutError:
                # Sin actividad en 60s — enviar ping para verificar que sigue vivo
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
                continue

            # Responder pings del cliente
            if isinstance(data, dict) and data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info("WS clean disconnect user=%s tenant=%s", user_id, tenant_id)
    except Exception as exc:
        logger.warning("WS error user=%s: %s", user_id, exc)
    finally:
        await manager.disconnect(client)

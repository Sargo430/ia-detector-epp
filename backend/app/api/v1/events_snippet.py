"""
events.py — snippet de integración
------------------------------------
Muestra cómo agregar publish_alert al endpoint POST /events existente,
para que cada evento ingestado desde el edge se retransmita en tiempo real
a los clientes WebSocket del tenant.

Solo se muestran las líneas relevantes al cambio — no es el archivo completo.
"""

from fastapi        import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.api.deps               import get_db, get_redis, OperatorUser
from app.schemas.event           import EventCreate, EventRead
from app.services.event              import crud_event
# ← NEW
from app.websockets.redis_subscriber import publish_alert

router = APIRouter(prefix="/events")


@router.post("/", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def ingest_event(
    payload:   EventCreate,
    db:        AsyncSession  = Depends(get_db),
    redis:     aioredis.Redis = Depends(get_redis),
    current:   OperatorUser  = Depends(),   # alias RBAC existente
):
    # 1. Persistir en BD (lógica existente)
    event = await crud_event.create(db, obj_in=payload, tenant_id=current.tenant_id)

    # ← NEW: 2. Publicar en Redis → retransmitido a todos los WS del tenant
    await publish_alert(redis, tenant_id=current.tenant_id, payload={
        "event_type":  event.event_type,
        "event_id":    str(event.id),
        "camera_id":   event.camera_id,
        "camera_name": event.camera_name,
        "zone":        event.zone,
        "severity":    event.severity,
        "confidence":  event.confidence,
        "ts":          event.created_at.isoformat(),
        # El thumbnail/clip NO se envía por WS — el cliente lo pide
        # con un GET presigned URL a MinIO cuando necesita verlo.
    })

    return event

import json
import asyncio
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from app.api.deps import CurrentUser
from app.services.redis import subscribe_alerts

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/stream")
async def stream_alerts(request: Request, current_user: CurrentUser):
    """
    Server-Sent Events endpoint — dashboard connects here to receive
    real-time alerts for the tenant.
    """
    tenant_slug = current_user["tenant"]

    async def event_generator():
        async for alert in subscribe_alerts(tenant_slug):
            if await request.is_disconnected():
                break
            yield f"data: {json.dumps(alert)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

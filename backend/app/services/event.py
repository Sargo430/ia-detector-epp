"""
Event service — ingest, query, review, and enrich with S3 pre-signed URLs.
"""
import uuid
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.alert import Alert
from app.schemas.event import EventIngest, EventFilter, EventResponse
from app.services import storage as s3
from app.services.redis import publish_alert
from app.workers.tasks.notifications import send_alert
from app.core.config import settings


async def ingest_event(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    tenant_slug: str,
    data: EventIngest,
) -> Event:
    event = Event(
        tenant_id=tenant_id,
        camera_id=data.camera_id,
        event_type=data.event_type,
        confidence=data.confidence,
        occurred_at=data.occurred_at,
        frame_s3_key=data.frame_s3_key,
        clip_s3_key=data.clip_s3_key,
        bounding_boxes=[bb.model_dump() for bb in data.bounding_boxes],
        raw_inference=data.raw_inference,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)

    # ── Auto-alert if confidence is high enough ───────────────────────────────
    await _maybe_fire_alert(db, event, tenant_slug)

    return event


async def _maybe_fire_alert(
    db: AsyncSession, event: Event, tenant_slug: str
) -> None:
    """Create an Alert record + push to Redis + queue notification worker."""
    HIGH_CONFIDENCE = 0.80
    if event.confidence < HIGH_CONFIDENCE:
        return

    severity = (
        "critical" if event.confidence >= 0.95
        else "high" if event.confidence >= 0.90
        else "medium"
    )

    alert = Alert(
        tenant_id=event.tenant_id,
        event_id=event.id,
        severity=severity,
        channel="dashboard",
        payload={
            "event_type": event.event_type,
            "camera_id": str(event.camera_id),
            "confidence": event.confidence,
            "occurred_at": event.occurred_at.isoformat(),
            "frame_s3_key": event.frame_s3_key,
        },
    )
    db.add(alert)
    await db.flush()

    # Push to Redis pub/sub (SSE dashboard) — fire & forget
    alert_payload = {
        "alert_id": str(alert.id),
        "event_id": str(event.id),
        "severity": severity,
        **alert.payload,
    }
    # Celery task handles Redis publish + email/webhook if configured
    send_alert.delay(tenant_slug, alert_payload)


async def get_event(
    db: AsyncSession, tenant_id: uuid.UUID, event_id: uuid.UUID
) -> Event | None:
    result = await db.execute(
        select(Event).where(
            Event.id == event_id,
            Event.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def list_events(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    filters: EventFilter,
    page: int = 1,
    page_size: int = 20,
) -> tuple[int, list[Event]]:
    conditions = [Event.tenant_id == tenant_id]

    if filters.camera_id:
        conditions.append(Event.camera_id == filters.camera_id)
    if filters.event_type:
        conditions.append(Event.event_type == filters.event_type)
    if filters.confidence_min is not None:
        conditions.append(Event.confidence >= filters.confidence_min)
    if filters.reviewed is not None:
        conditions.append(Event.reviewed == filters.reviewed)
    if filters.from_dt:
        conditions.append(Event.occurred_at >= filters.from_dt)
    if filters.to_dt:
        conditions.append(Event.occurred_at <= filters.to_dt)

    q = select(Event).where(and_(*conditions))
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    events = await db.execute(
        q.order_by(Event.occurred_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return total or 0, list(events.scalars().all())


async def mark_reviewed(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    event_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> Event | None:
    event = await get_event(db, tenant_id, event_id)
    if not event:
        return None
    event.reviewed = True
    event.reviewed_by = reviewer_id
    await db.flush()
    await db.refresh(event)
    return event


async def enrich_with_urls(event: Event) -> dict:
    """Attach pre-signed S3 URLs to the event dict for the response."""
    data = EventResponse.model_validate(event).model_dump()
    if event.frame_s3_key:
        data["frame_url"] = await s3.presign_get(settings.S3_FRAMES_BUCKET, event.frame_s3_key)
    if event.clip_s3_key:
        data["clip_url"] = await s3.presign_get(settings.S3_CLIPS_BUCKET, event.clip_s3_key)
    return data

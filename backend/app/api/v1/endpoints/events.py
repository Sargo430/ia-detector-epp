import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func, and_

from app.api.deps import TenantDB, CurrentUser, OperatorUser
from app.schemas.event import (
    EventIngest, EventFilter,
    EventResponse, EventListResponse,
)
from app.services import event as svc
from app.models.event import Event

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/ingest", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def ingest_event(body: EventIngest, db: TenantDB, user: OperatorUser):
    """
    Main write path — called by the inference worker each time the model
    produces a detection. Auto-fires alert if confidence >= 0.80.
    """
    from app.db.tenant import tenant_schema_name
    # tenant_slug is encoded in the token; retrieve from DB context
    event = await svc.ingest_event(db, user.tenant_id, str(user.tenant_id), body)
    return await svc.enrich_with_urls(event)


@router.get("", response_model=EventListResponse)
async def list_events(
    db: TenantDB,
    user: CurrentUser,
    camera_id: uuid.UUID | None = Query(None),
    event_type: str | None = Query(None),
    confidence_min: float | None = Query(None, ge=0.0, le=1.0),
    reviewed: bool | None = Query(None),
    from_dt: datetime | None = Query(None),
    to_dt: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = EventFilter(
        camera_id=camera_id,
        event_type=event_type,
        confidence_min=confidence_min,
        reviewed=reviewed,
        from_dt=from_dt,
        to_dt=to_dt,
    )
    total, events = await svc.list_events(db, user.tenant_id, filters, page, page_size)
    enriched = [await svc.enrich_with_urls(e) for e in events]
    return EventListResponse(total=total, page=page, page_size=page_size, items=enriched)


@router.get("/stats/summary")
async def event_stats(
    db: TenantDB,
    user: CurrentUser,
    from_dt: datetime | None = Query(None),
    to_dt: datetime | None = Query(None),
):
    """Breakdown by event type — feeds dashboard charts."""
    conditions = [Event.tenant_id == user.tenant_id]
    if from_dt:
        conditions.append(Event.occurred_at >= from_dt)
    if to_dt:
        conditions.append(Event.occurred_at <= to_dt)

    result = await db.execute(
        select(
            Event.event_type,
            func.count(Event.id).label("count"),
            func.avg(Event.confidence).label("avg_confidence"),
            func.count(Event.id).filter(Event.reviewed == False).label("unreviewed"),
        )
        .where(and_(*conditions))
        .group_by(Event.event_type)
    )
    rows = result.all()
    return {
        "total": sum(r.count for r in rows),
        "by_type": [
            {
                "event_type": r.event_type,
                "count": r.count,
                "avg_confidence": round(r.avg_confidence or 0, 3),
                "unreviewed": r.unreviewed,
            }
            for r in rows
        ],
    }


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: uuid.UUID, db: TenantDB, user: CurrentUser):
    event = await svc.get_event(db, user.tenant_id, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return await svc.enrich_with_urls(event)


@router.post("/{event_id}/review", response_model=EventResponse)
async def review_event(event_id: uuid.UUID, db: TenantDB, user: OperatorUser):
    """Mark an event as reviewed. Operator or Admin."""
    event = await svc.mark_reviewed(db, user.tenant_id, event_id, user.id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return await svc.enrich_with_urls(event)

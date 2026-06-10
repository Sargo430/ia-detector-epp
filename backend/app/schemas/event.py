from uuid import UUID
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field
from app.schemas.common import UUIDSchema, TimestampSchema

EventType = Literal["intrusion", "fire", "crowd", "object_left", "face_match", "other"]
Severity   = Literal["low", "medium", "high", "critical"]


# ── Request bodies ────────────────────────────────────────────────────────────
class BoundingBox(BaseModel):
    x: float
    y: float
    w: float
    h: float
    label: str
    confidence: float


class EventIngest(BaseModel):
    """
    Payload sent by the inference worker (or edge device) to register a detection.
    This is the main write path: model → POST /events/ingest
    """
    camera_id: UUID
    event_type: EventType
    confidence: float = Field(..., ge=0.0, le=1.0)
    occurred_at: datetime
    frame_s3_key: str | None = None
    clip_s3_key: str | None = None
    bounding_boxes: list[BoundingBox] = []
    raw_inference: dict[str, Any] = {}


class EventReview(BaseModel):
    reviewed: bool = True


class EventFilter(BaseModel):
    camera_id: UUID | None = None
    event_type: EventType | None = None
    confidence_min: float | None = None
    reviewed: bool | None = None
    from_dt: datetime | None = None
    to_dt: datetime | None = None


# ── Responses ─────────────────────────────────────────────────────────────────
class EventResponse(UUIDSchema, TimestampSchema):
    tenant_id: UUID
    camera_id: UUID
    event_type: str
    confidence: float
    occurred_at: datetime
    frame_s3_key: str | None
    clip_s3_key: str | None
    bounding_boxes: list[dict]
    reviewed: bool
    reviewed_by: UUID | None

    # pre-signed URLs injected by the service layer (not stored in DB)
    frame_url: str | None = None
    clip_url: str | None = None


class EventListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[EventResponse]

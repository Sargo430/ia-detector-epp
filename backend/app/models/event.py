from datetime import datetime
from sqlalchemy import String, Float, JSON, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, UUIDMixin, TimestampMixin
import uuid


class Event(Base, UUIDMixin, TimestampMixin):
    """A detection event produced by the ML model."""
    __tablename__ = "events"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    camera_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    # e.g. intrusion | fire | crowd | object_left | face_match
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    frame_s3_key: Mapped[str] = mapped_column(String(512), nullable=True)   # S3 key for thumbnail
    clip_s3_key: Mapped[str] = mapped_column(String(512), nullable=True)    # S3 key for video clip
    bounding_boxes: Mapped[list] = mapped_column(JSON, default=list)
    raw_inference: Mapped[dict] = mapped_column(JSON, default=dict)
    reviewed: Mapped[bool] = mapped_column(default=False)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

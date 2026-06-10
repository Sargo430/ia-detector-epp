from sqlalchemy import String, Boolean, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, UUIDMixin, TimestampMixin
import uuid


class Camera(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cameras"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    rtsp_url: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    fps: Mapped[float] = mapped_column(Float, default=15.0)
    resolution: Mapped[str] = mapped_column(String(20), default="1280x720")
    detection_config: Mapped[dict] = mapped_column(JSON, default=dict)  # model thresholds, zones
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

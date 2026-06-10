from uuid import UUID
from typing import Any
from pydantic import BaseModel, field_validator
from app.schemas.common import UUIDSchema, TimestampSchema


# ── Detection config sub-schema ───────────────────────────────────────────────
class DetectionConfig(BaseModel):
    confidence_threshold: float = 0.6
    event_types: list[str] = ["intrusion", "fire", "crowd"]
    zones: list[dict[str, Any]] = []   # [{name, polygon: [[x,y],...]}]
    alert_cooldown_seconds: int = 30   # min seconds between alerts for same type


# ── Request bodies ────────────────────────────────────────────────────────────
class CameraCreate(BaseModel):
    name: str
    location: str | None = None
    rtsp_url: str
    fps: float = 15.0
    resolution: str = "1280x720"
    detection_config: DetectionConfig = DetectionConfig()

    @field_validator("fps")
    @classmethod
    def validate_fps(cls, v):
        if not 1 <= v <= 60:
            raise ValueError("fps must be between 1 and 60")
        return v

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, v):
        parts = v.split("x")
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            raise ValueError("resolution must be WxH e.g. 1280x720")
        return v


class CameraUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    rtsp_url: str | None = None
    fps: float | None = None
    resolution: str | None = None
    is_active: bool | None = None
    detection_config: DetectionConfig | None = None


# ── Responses ─────────────────────────────────────────────────────────────────
class CameraResponse(UUIDSchema, TimestampSchema):
    tenant_id: UUID
    name: str
    location: str | None
    rtsp_url: str
    is_active: bool
    fps: float
    resolution: str
    detection_config: dict


class CameraListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[CameraResponse]

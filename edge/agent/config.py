import json
from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DetectionConfig(BaseModel):
    confidence_threshold: float = 0.60
    event_types: list[str] = ["intrusion"]
    zones: list[dict] = []


class CameraConfig(BaseModel):
    id: str
    name: str
    rtsp_url: str
    fps_capture: int = 15
    enabled: bool = True
    detection_config: DetectionConfig = DetectionConfig()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # API
    API_BASE_URL: str = "http://localhost:8000/api/v1"
    TENANT_SLUG: str = "acme"
    API_EMAIL: str = "agent@acme.com"
    API_PASSWORD: str = "AgentPass1"

    # Cameras
    CAMERAS_CONFIG_FILE: str = "config/cameras.json"

    # Model
    MODEL_PATH: str = "models/best.pt"
    MODEL_DEVICE: str = "cpu"
    MODEL_IMG_SIZE: int = 640
    MODEL_CONFIDENCE: float = 0.60
    MODEL_IOU: float = 0.45

    # Pipeline
    FRAME_SKIP: int = 5
    BATCH_SIZE: int = 4
    FRAME_QUEUE_MAX: int = 100

    # S3
    S3_ENDPOINT_URL: str | None = None
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_REGION: str = "us-east-1"
    S3_FRAMES_BUCKET: str = "frames"
    S3_CLIPS_BUCKET: str = "clips"

    # Clip
    CLIP_PRE_SECONDS: int = 3
    CLIP_POST_SECONDS: int = 5
    CLIP_ENABLED: bool = True

    # Resilience
    API_RETRY_ATTEMPTS: int = 5
    API_RETRY_WAIT_SECONDS: int = 2
    RTSP_RECONNECT_DELAY: int = 5

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    def load_cameras(self) -> list[CameraConfig]:
        path = Path(self.CAMERAS_CONFIG_FILE)
        if not path.exists():
            raise FileNotFoundError(f"Cameras config not found: {path}")
        data = json.loads(path.read_text())
        return [CameraConfig(**cam) for cam in data if cam.get("enabled", True)]


settings = Settings()

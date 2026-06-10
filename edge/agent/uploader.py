"""
Upload directo a MinIO/S3 usando URLs pre-firmadas.
El frame nunca pasa por el backend — va directo al bucket.
"""
import io
import cv2
import boto3
import numpy as np
from botocore.config import Config

from agent.config import settings
from utils.logger import get_logger

log = get_logger("uploader")

_s3 = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT_URL or None,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
    region_name=settings.S3_REGION,
    config=Config(signature_version="s3v4"),
)


def encode_frame_jpeg(frame: np.ndarray, quality: int = 85) -> bytes:
    """Codifica un frame OpenCV a JPEG en memoria."""
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError("Frame encoding failed")
    return buf.tobytes()


def upload_frame(presign_url: str, frame: np.ndarray) -> None:
    """PUT del frame JPEG a la URL pre-firmada."""
    import urllib.request
    data = encode_frame_jpeg(frame)
    req = urllib.request.Request(
        presign_url,
        data=data,
        method="PUT",
        headers={"Content-Type": "image/jpeg"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status not in (200, 204):
            raise RuntimeError(f"Upload failed: HTTP {resp.status}")
    log.debug("uploader.frame.ok", size=len(data))


def upload_clip(presign_url: str, clip_path: str) -> None:
    """PUT de un archivo de video a la URL pre-firmada."""
    import urllib.request
    with open(clip_path, "rb") as f:
        data = f.read()
    req = urllib.request.Request(
        presign_url,
        data=data,
        method="PUT",
        headers={"Content-Type": "video/mp4"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        if resp.status not in (200, 204):
            raise RuntimeError(f"Clip upload failed: HTTP {resp.status}")
    log.info("uploader.clip.ok", size=len(data))

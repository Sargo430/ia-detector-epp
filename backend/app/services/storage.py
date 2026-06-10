"""
S3 / MinIO pre-signed URL generator.
Works with both AWS S3 (endpoint_url=None) and MinIO.
"""
import aioboto3
from app.core.config import settings

_session = aioboto3.Session()


def _client():
    return _session.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL or None,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
    )


async def presign_get(bucket: str, key: str, expires: int = 3600) -> str:
    """Return a pre-signed GET URL valid for `expires` seconds."""
    async with _client() as s3:
        url = await s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires,
        )
    return url


async def presign_put(bucket: str, key: str, expires: int = 900) -> str:
    """Return a pre-signed PUT URL for direct upload from edge device."""
    async with _client() as s3:
        url = await s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires,
        )
    return url


async def delete_object(bucket: str, key: str) -> None:
    async with _client() as s3:
        await s3.delete_object(Bucket=bucket, Key=key)


def frame_key(tenant_slug: str, camera_id: str, event_id: str) -> str:
    return f"{tenant_slug}/frames/{camera_id}/{event_id}.jpg"


def clip_key(tenant_slug: str, camera_id: str, event_id: str) -> str:
    return f"{tenant_slug}/clips/{camera_id}/{event_id}.mp4"

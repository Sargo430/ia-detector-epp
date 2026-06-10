import uuid
from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import TenantDB, CurrentUser, OperatorUser, AdminUser
from app.schemas.camera import (
    CameraCreate, CameraUpdate,
    CameraResponse, CameraListResponse,
)
from app.services import camera as svc

router = APIRouter(prefix="/cameras", tags=["cameras"])


@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(body: CameraCreate, db: TenantDB, user: AdminUser):
    """Register a new camera. Admin only."""
    camera = await svc.create_camera(db, user.tenant_id, body)
    return camera


@router.get("", response_model=CameraListResponse)
async def list_cameras(
    db: TenantDB,
    user: CurrentUser,
    is_active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    total, cameras = await svc.list_cameras(db, user.tenant_id, is_active, page, page_size)
    return CameraListResponse(total=total, page=page, page_size=page_size, items=cameras)


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(camera_id: uuid.UUID, db: TenantDB, user: CurrentUser):
    camera = await svc.get_camera(db, user.tenant_id, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera


@router.patch("/{camera_id}", response_model=CameraResponse)
async def update_camera(camera_id: uuid.UUID, body: CameraUpdate, db: TenantDB, user: AdminUser):
    camera = await svc.update_camera(db, user.tenant_id, camera_id, body)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(camera_id: uuid.UUID, db: TenantDB, user: AdminUser):
    deleted = await svc.delete_camera(db, user.tenant_id, camera_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Camera not found")


@router.post("/{camera_id}/activate", response_model=CameraResponse)
async def activate_camera(camera_id: uuid.UUID, db: TenantDB, user: OperatorUser):
    camera = await svc.toggle_camera(db, user.tenant_id, camera_id, active=True)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera


@router.post("/{camera_id}/deactivate", response_model=CameraResponse)
async def deactivate_camera(camera_id: uuid.UUID, db: TenantDB, user: OperatorUser):
    camera = await svc.toggle_camera(db, user.tenant_id, camera_id, active=False)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera


@router.get("/{camera_id}/presign-upload")
async def presign_upload(
    camera_id: uuid.UUID,
    filename: str = Query(...),
    db: TenantDB = None,
    user: OperatorUser = None,
):
    from app.services.storage import presign_put, frame_key, clip_key
    from app.core.config import settings
    tenant_slug = user.tenant_id  # use tenant_id; slug comes from token context
    is_clip = filename.endswith(".mp4")
    bucket = settings.S3_CLIPS_BUCKET if is_clip else settings.S3_FRAMES_BUCKET
    key = (
        clip_key(str(user.tenant_id), str(camera_id), filename)
        if is_clip
        else frame_key(str(user.tenant_id), str(camera_id), filename)
    )
    url = await presign_put(bucket, key)
    return {"upload_url": url, "s3_key": key, "bucket": bucket}

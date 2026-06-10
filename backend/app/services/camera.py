"""
Camera service — all DB operations for cameras.
Receives a tenant-scoped AsyncSession from the dependency layer.
"""
import uuid
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.camera import Camera
from app.schemas.camera import CameraCreate, CameraUpdate


async def create_camera(
    db: AsyncSession, tenant_id: uuid.UUID, data: CameraCreate
) -> Camera:
    camera = Camera(
        tenant_id=tenant_id,
        name=data.name,
        location=data.location,
        rtsp_url=data.rtsp_url,
        fps=data.fps,
        resolution=data.resolution,
        detection_config=data.detection_config.model_dump(),
    )
    db.add(camera)
    await db.flush()
    await db.refresh(camera)
    return camera


async def get_camera(
    db: AsyncSession, tenant_id: uuid.UUID, camera_id: uuid.UUID
) -> Camera | None:
    result = await db.execute(
        select(Camera).where(
            Camera.id == camera_id,
            Camera.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def list_cameras(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    is_active: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[int, list[Camera]]:
    q = select(Camera).where(Camera.tenant_id == tenant_id)
    if is_active is not None:
        q = q.where(Camera.is_active == is_active)

    total = await db.scalar(
        select(func.count()).select_from(q.subquery())
    )
    cameras = await db.execute(
        q.order_by(Camera.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return total or 0, list(cameras.scalars().all())


async def update_camera(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    camera_id: uuid.UUID,
    data: CameraUpdate,
) -> Camera | None:
    camera = await get_camera(db, tenant_id, camera_id)
    if not camera:
        return None

    patch = data.model_dump(exclude_unset=True)
    if "detection_config" in patch and patch["detection_config"]:
        patch["detection_config"] = data.detection_config.model_dump()

    for field, value in patch.items():
        setattr(camera, field, value)

    await db.flush()
    await db.refresh(camera)
    return camera


async def delete_camera(
    db: AsyncSession, tenant_id: uuid.UUID, camera_id: uuid.UUID
) -> bool:
    camera = await get_camera(db, tenant_id, camera_id)
    if not camera:
        return False
    await db.delete(camera)
    await db.flush()
    return True


async def toggle_camera(
    db: AsyncSession, tenant_id: uuid.UUID, camera_id: uuid.UUID, active: bool
) -> Camera | None:
    camera = await get_camera(db, tenant_id, camera_id)
    if not camera:
        return None
    camera.is_active = active
    await db.flush()
    await db.refresh(camera)
    return camera

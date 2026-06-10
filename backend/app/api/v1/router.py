from fastapi import APIRouter
from app.api.v1.endpoints import health, alerts, auth, cameras, events

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(cameras.router)
api_router.include_router(events.router)
api_router.include_router(alerts.router)

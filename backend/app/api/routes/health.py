from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def get_health() -> dict:
    return {
        "status": "ok",
        "service": "alphacouncil-api",
        "version": settings.version,
    }

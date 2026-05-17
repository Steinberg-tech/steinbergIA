from fastapi import APIRouter

from config.settings import settings
from observability import metrics

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": settings.app_version,
        "env": settings.app_env,
    }


@router.get("/metrics")
async def get_metrics():
    return metrics.snapshot()

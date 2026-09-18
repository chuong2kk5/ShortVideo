from fastapi import APIRouter
from app.api.routes_system import router as system_router
from app.api.routes_projects import router as projects_router
from app.api.routes_pipeline import router as pipeline_router
from app.api.routes_youtube import router as youtube_router
from app.api.routes_tts import router as tts_router

api_router = APIRouter(prefix="/api")
api_router.include_router(system_router)
api_router.include_router(projects_router)
api_router.include_router(pipeline_router)
api_router.include_router(youtube_router)
api_router.include_router(tts_router)

__all__ = ["api_router"]



import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings, BASE_DIR
from app.core.database import init_db, engine
from app.core.memory_guard import memory_guard
from app.api import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info("Initializing AI Shorts Factory & YouTube Manager Backend...")

    # 1. Ensure storage directories exist
    settings.get_outputs_path()
    settings.get_temp_path()
    settings.get_brand_kits_path()
    settings.get_uploads_path()

    # 2. Initialize SQLite tables
    logger.info("Initializing SQLite database...")
    await init_db()
    logger.info("Database initialized successfully.")

    # 3. Log hardware memory stats
    health = memory_guard.get_full_health()
    logger.info(
        f"Hardware Detection -> RAM: {health['ram']['used_mb']}/{health['ram']['total_mb']} MB ({health['ram']['percent']}%), "
        f"GPU: {health['vram']['gpu_name']} ({health['vram']['used_mb']}/{health['vram']['total_mb']} MB)"
    )

    yield

    # --- Shutdown ---
    logger.info("Shutting down AI Shorts Factory Backend...")
    await engine.dispose()
    logger.info("Database connection pool closed.")


app = FastAPI(
    title="AI Shorts Factory & YouTube Manager",
    description="Automated AI Video Creation Pipeline & Multi-Channel YouTube Manager Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for outputs and uploads
outputs_dir = settings.get_outputs_path()
app.mount("/static/outputs", StaticFiles(directory=str(outputs_dir)), name="outputs")

uploads_dir = settings.get_uploads_path()
app.mount("/static/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Mount API routes
app.include_router(api_router)

# Mount Frontend Dist if built
frontend_dist = BASE_DIR.parent / "frontend" / "dist"
if frontend_dist.exists():
    from fastapi.responses import FileResponse
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="frontend_assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/")
    async def root():
        return {
            "app": "AI Shorts Factory & YouTube Manager",
            "version": "1.0.0",
            "status": "online",
            "docs_url": "/docs",
            "hardware_guard": {
                "ram_percent": memory_guard.get_system_ram_metrics()["percent"],
                "gpu": memory_guard.get_gpu_vram_metrics()["gpu_name"],
                "active_stage": memory_guard.current_stage or "idle",
            },
        }


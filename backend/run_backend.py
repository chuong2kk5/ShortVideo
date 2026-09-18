import os
import sys
from pathlib import Path
import uvicorn

# Add backend directory to sys.path so 'app' imports correctly
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from app.config import settings

if __name__ == "__main__":
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("=" * 70)
    print(" AI SHORTS FACTORY & YOUTUBE MANAGER - BACKEND SERVER")
    print(f" Host: http://{settings.HOST}:{settings.PORT}")
    print(f" Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print("=" * 70)

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )

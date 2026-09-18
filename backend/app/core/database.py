from pathlib import Path
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from app.config import settings, BASE_DIR

# Ensure database directory exists
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite+aiosqlite:///"):
    sqlite_rel_path = db_url.replace("sqlite+aiosqlite:///", "")
    db_file_path = (BASE_DIR / sqlite_rel_path).resolve()
    db_file_path.parent.mkdir(parents=True, exist_ok=True)
    # Normalized connection URL
    normalized_db_url = f"sqlite+aiosqlite:///{db_file_path.as_posix()}"
else:
    normalized_db_url = db_url

engine = create_async_engine(
    normalized_db_url,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing an async database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    # Import all models here so Base knows about them before create_all
    import app.models.db_models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Safe migration for new columns
        try:
            from sqlalchemy import text
            await conn.execute(text("ALTER TABLE scenes ADD COLUMN visual_keywords VARCHAR(256)"))
        except Exception:
            pass  # Column already exists


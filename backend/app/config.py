import os
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server Settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"

    # Storage Paths
    OUTPUTS_DIR: str = "./data/outputs"
    TEMP_CACHE_DIR: str = "./data/temp"
    BRAND_KITS_DIR: str = "./data/brand_kits"
    UPLOADS_DIR: str = "./data/uploads"

    # Hardware Memory Guard Thresholds
    MAX_RAM_PERCENT_THRESHOLD: float = 85.0
    MAX_VRAM_MB_THRESHOLD: float = 5500.0
    FORCE_GC_AFTER_EACH_STAGE: bool = True
    UNLOAD_MODEL_AFTER_STAGE: bool = True

    # LLM Settings
    LLM_PROVIDER: str = "ollama"  # "ollama" | "openai" | "gemini"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b-instruct"
    OLLAMA_KEEP_ALIVE: str = "0s"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 8192

    # Cloud LLM Options
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Phase 2 Engine Placeholders
    COMFYUI_BASE_URL: str = "http://localhost:8188"
    COMFYUI_WORKFLOW_PRESET: str = "flux_schnell_fast"
    TTS_ENGINE_DEFAULT: str = "edge_tts"
    EDGE_TTS_VOICE: str = "vi-VN-NamMinhNeural"
    TTS_SPEED_RATE: str = "+22%"
    FFMPEG_PATH: str = "ffmpeg"

    # Video & Visual Asset Stock Keys
    PEXELS_API_KEY: str = ""

    # Phase 3 YouTube Settings
    YOUTUBE_CLIENT_SECRETS_FILE: str = "./data/client_secrets.json"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    def resolve_path(self, relative_path: str) -> Path:
        """Resolve a path relative to the backend root directory."""
        path = Path(relative_path)
        if path.is_absolute():
            return path
        return (BASE_DIR / path).resolve()

    def get_outputs_path(self) -> Path:
        p = self.resolve_path(self.OUTPUTS_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def get_temp_path(self) -> Path:
        p = self.resolve_path(self.TEMP_CACHE_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def get_brand_kits_path(self) -> Path:
        p = self.resolve_path(self.BRAND_KITS_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def get_uploads_path(self) -> Path:
        p = self.resolve_path(self.UPLOADS_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()


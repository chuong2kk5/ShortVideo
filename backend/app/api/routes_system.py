import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings, BASE_DIR
from app.core.memory_guard import memory_guard
from app.models.schemas import SystemHealthResponse
from app.orchestrator.llm_client import llm_client

logger = logging.getLogger("routes_system")
router = APIRouter(prefix="/system", tags=["System & Memory Guard"])


class AIConfigUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    llm_provider: Optional[str] = None
    ollama_model: Optional[str] = None
    ollama_base_url: Optional[str] = None


class GeminiTestRequest(BaseModel):
    gemini_api_key: Optional[str] = None


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health():
    """Get real-time RAM and VRAM status along with active pipeline stage."""
    return memory_guard.get_full_health()


@router.post("/free-memory")
async def free_memory():
    """Explicitly trigger memory cleanup (unload models, empty PyTorch CUDA cache, run GC)."""
    cleanup_report = await memory_guard.free_memory(unload_llm=True)
    return {
        "status": "success",
        "message": "Memory cleanup successfully executed.",
        "report": cleanup_report,
    }


@router.get("/llm-status")
async def get_llm_status():
    """Check availability of configured LLM provider (Ollama, OpenAI, or Gemini)."""
    return await llm_client.check_availability()


@router.get("/ai-status")
async def get_comprehensive_ai_status():
    """
    Returns complete status for Ollama, Gemini, and ComfyUI for UI configuration modal.
    """
    env_file = BASE_DIR / ".env"
    env_vars: Dict[str, str] = {}
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip("'\"")

    # 1. Check Ollama
    ollama_url = env_vars.get("OLLAMA_BASE_URL", settings.OLLAMA_BASE_URL).rstrip("/")
    ollama_online = False
    ollama_models = []
    try:
        async with httpx.AsyncClient(timeout=2.5) as client:
            res = await client.get(f"{ollama_url}/api/tags")
            if res.status_code == 200:
                ollama_online = True
                ollama_models = [m.get("name") for m in res.json().get("models", [])]
    except Exception:
        pass

    # 2. Check Gemini Key
    gemini_key = env_vars.get("GEMINI_API_KEY", settings.GEMINI_API_KEY)
    gemini_configured = bool(gemini_key and len(gemini_key) > 8)
    masked_gemini_key = (
        f"{gemini_key[:4]}...{gemini_key[-4:]}" if gemini_configured else ""
    )

    # 3. Check ComfyUI
    comfyui_url = env_vars.get("COMFYUI_BASE_URL", settings.COMFYUI_BASE_URL).rstrip("/")
    comfyui_online = False
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            c_res = await client.get(f"{comfyui_url}/system_stats")
            comfyui_online = c_res.status_code == 200
    except Exception:
        pass

    return {
        "ollama": {
            "online": ollama_online,
            "url": ollama_url,
            "models": ollama_models,
            "active_model": env_vars.get("OLLAMA_MODEL", settings.OLLAMA_MODEL),
        },
        "gemini": {
            "configured": gemini_configured,
            "masked_key": masked_gemini_key,
            "model": env_vars.get("GEMINI_MODEL", settings.GEMINI_MODEL),
        },
        "comfyui": {
            "online": comfyui_online,
            "url": comfyui_url,
        },
        "llm_provider": env_vars.get("LLM_PROVIDER", settings.LLM_PROVIDER),
    }


@router.post("/save-ai-config")
async def save_ai_config(payload: AIConfigUpdateRequest):
    """
    Saves AI API keys and provider preferences directly to backend/.env file on disk.
    Immediately takes effect for new pipeline runs without server restart!
    """
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        env_file = BASE_DIR / ".env.example"

    content = env_file.read_text(encoding="utf-8") if env_file.exists() else ""

    def update_key(text: str, key: str, value: str) -> str:
        pattern = rf"^{key}=.*$"
        replacement = f"{key}={value}"
        if re.search(pattern, text, flags=re.MULTILINE):
            return re.sub(pattern, replacement, text, flags=re.MULTILINE)
        else:
            return text + f"\n{key}={value}"

    if payload.gemini_api_key is not None:
        content = update_key(content, "GEMINI_API_KEY", payload.gemini_api_key.strip())
        settings.GEMINI_API_KEY = payload.gemini_api_key.strip()

    if payload.llm_provider is not None:
        content = update_key(content, "LLM_PROVIDER", payload.llm_provider.strip().lower())
        settings.LLM_PROVIDER = payload.llm_provider.strip().lower()

    if payload.ollama_model is not None:
        content = update_key(content, "OLLAMA_MODEL", payload.ollama_model.strip())
        settings.OLLAMA_MODEL = payload.ollama_model.strip()

    if payload.ollama_base_url is not None:
        content = update_key(content, "OLLAMA_BASE_URL", payload.ollama_base_url.strip())
        settings.OLLAMA_BASE_URL = payload.ollama_base_url.strip()

    target_path = BASE_DIR / ".env"
    target_path.write_text(content, encoding="utf-8")
    logger.info("Successfully updated backend/.env configuration.")

    return {
        "status": "success",
        "message": "Cấu hình AI đã được lưu thành công vào backend/.env!",
    }


@router.post("/test-gemini")
async def test_gemini_connection(payload: GeminiTestRequest):
    """
    Tests and auto-detects a working Gemini model using the provided or configured API key.
    Automatically discovers supported models (ListModels API) and binds to the active model.
    """
    from app.services.gemini_service import auto_detect_gemini_model

    env_file = BASE_DIR / ".env"
    key = payload.gemini_api_key.strip() if payload.gemini_api_key else ""
    if not key and env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("GEMINI_API_KEY="):
                key = line.split("=", 1)[1].strip().strip("'\"")
                break

    if not key:
        raise HTTPException(
            status_code=400,
            detail="Vui lòng nhập hoặc dán GEMINI_API_KEY để kiểm tra!",
        )

    preferred_model = settings.GEMINI_MODEL
    success, message, working_model = await auto_detect_gemini_model(
        api_key=key,
        preferred_model=preferred_model,
    )

    if success:
        return {
            "status": "success",
            "valid": True,
            "message": message,
            "active_model": working_model,
        }
    else:
        return {
            "status": "error",
            "valid": False,
            "message": message,
        }

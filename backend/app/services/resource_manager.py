import asyncio
import gc
import logging
import shutil
import subprocess
from typing import Dict, Any, Optional
import httpx
import psutil

from app.config import settings

logger = logging.getLogger("resource_manager")


class ResourceManager:
    """
    Hardware Memory Guard & Resource Allocator.
    Enforces sequential pipeline stages on Windows (16GB RAM / 4-6GB VRAM)
    and actively purges memory and models after each stage.
    """

    def __init__(self):
        self._lock = asyncio.Lock()
        self._current_stage: Optional[str] = None

    @property
    def current_stage(self) -> Optional[str]:
        return self._current_stage

    def get_ram_info(self) -> Dict[str, Any]:
        """Returns system RAM metrics via psutil."""
        vm = psutil.virtual_memory()
        return {
            "total_mb": round(vm.total / (1024 * 1024), 2),
            "available_mb": round(vm.available / (1024 * 1024), 2),
            "used_mb": round(vm.used / (1024 * 1024), 2),
            "percent": vm.percent,
            "is_safe": vm.percent < settings.MAX_RAM_PERCENT_THRESHOLD,
        }

    def get_vram_info(self) -> Dict[str, Any]:
        """Returns NVIDIA GPU VRAM metrics via nvidia-smi."""
        nvidia_smi = shutil.which("nvidia-smi")
        if not nvidia_smi:
            return {
                "available": False,
                "gpu_name": "No NVIDIA GPU detected",
                "used_mb": 0,
                "total_mb": 0,
                "free_mb": 0,
                "percent": 0.0,
                "is_safe": True,
            }

        try:
            cmd = [
                nvidia_smi,
                "--query-gpu=name,memory.total,memory.used,memory.free",
                "--format=csv,noheader,nounits",
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=3
            )
            line = result.stdout.strip().split("\n")[0]
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 4:
                gpu_name = parts[0]
                total_mb = float(parts[1])
                used_mb = float(parts[2])
                free_mb = float(parts[3])
                percent = round((used_mb / total_mb) * 100, 2) if total_mb > 0 else 0.0
                return {
                    "available": True,
                    "gpu_name": gpu_name,
                    "total_mb": total_mb,
                    "used_mb": used_mb,
                    "free_mb": free_mb,
                    "percent": percent,
                    "is_safe": used_mb < settings.MAX_VRAM_MB_THRESHOLD,
                }
        except Exception as e:
            logger.debug(f"nvidia-smi query error: {e}")

        return {
            "available": False,
            "gpu_name": "NVIDIA SMI Query Failed",
            "used_mb": 0,
            "total_mb": 0,
            "free_mb": 0,
            "percent": 0.0,
            "is_safe": True,
        }

    def check_resources(self) -> Dict[str, Any]:
        """Comprehensive hardware health check."""
        ram = self.get_ram_info()
        vram = self.get_vram_info()
        return {
            "ram": ram,
            "vram": vram,
            "current_stage": self._current_stage or "idle",
            "ready_for_heavy_task": ram["is_safe"] and vram["is_safe"],
        }

    async def unload_models(self) -> Dict[str, Any]:
        """
        Actively offloads loaded models from RAM/VRAM:
        1. Sends Ollama unload request (keep_alive: 0).
        2. Calls ComfyUI free memory API if alive.
        3. Empties PyTorch CUDA cache.
        4. Triggers Python garbage collection.
        """
        logger.info("Executing ResourceManager.unload_models()...")
        ollama_unloaded = False
        comfyui_freed = False
        torch_cleared = False

        # 1. Unload Ollama
        try:
            url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.post(
                    url,
                    json={"model": settings.OLLAMA_MODEL, "keep_alive": 0},
                )
                if res.status_code == 200:
                    ollama_unloaded = True
                    logger.info("Ollama model successfully unloaded (keep_alive: 0).")
        except Exception:
            pass

        # 2. Free ComfyUI memory if reachable
        try:
            comfy_url = f"{settings.COMFYUI_BASE_URL.rstrip('/')}/free"
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.post(
                    comfy_url, json={"unload_models": True, "free_memory": True}
                )
                if res.status_code == 200:
                    comfyui_freed = True
                    logger.info("ComfyUI VRAM cache cleared.")
        except Exception:
            pass

        # 3. Torch CUDA cache
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
                torch_cleared = True
        except ImportError:
            pass

        # 4. Garbage Collection
        collected = gc.collect()

        return {
            "ollama_unloaded": ollama_unloaded,
            "comfyui_freed": comfyui_freed,
            "torch_cleared": torch_cleared,
            "gc_collected_objects": collected,
            "ram_after": self.get_ram_info(),
            "vram_after": self.get_vram_info(),
        }

    class StageContext:
        def __init__(self, manager: "ResourceManager", stage_name: str):
            self.manager = manager
            self.stage_name = stage_name

        async def __aenter__(self):
            await self.manager._lock.acquire()
            self.manager._current_stage = self.stage_name
            logger.info(f"==> STAGE LOCK ACQUIRED: [{self.stage_name}]")
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            try:
                logger.info(f"<== STAGE COMPLETED: [{self.stage_name}]. Releasing memory...")
                await self.manager.unload_models()
            finally:
                self.manager._current_stage = None
                self.manager._lock.release()
                logger.info(f"==> STAGE LOCK RELEASED: [{self.stage_name}]")

    def guard_stage(self, stage_name: str) -> "ResourceManager.StageContext":
        """Context manager to guarantee sequential processing & auto model purging."""
        return self.StageContext(self, stage_name)


resource_manager = ResourceManager()


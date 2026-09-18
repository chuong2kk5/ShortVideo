import asyncio
import gc
import logging
import shutil
import subprocess
from typing import Dict, Any, Optional
import httpx
import psutil

from app.config import settings

logger = logging.getLogger("memory_guard")


class MemoryGuard:
    """
    Hardware Memory Guard for Windows (16GB RAM / 4-6GB VRAM).
    Enforces sequential processing across pipeline stages and unloads
    models from VRAM/RAM immediately after task completion.
    """

    def __init__(self):
        self._lock = asyncio.Lock()
        self._current_stage: Optional[str] = None

    @property
    def current_stage(self) -> Optional[str]:
        return self._current_stage

    def get_system_ram_metrics(self) -> Dict[str, Any]:
        """Fetch system RAM metrics using psutil."""
        vm = psutil.virtual_memory()
        return {
            "total_mb": round(vm.total / (1024 * 1024), 2),
            "available_mb": round(vm.available / (1024 * 1024), 2),
            "used_mb": round(vm.used / (1024 * 1024), 2),
            "percent": vm.percent,
            "status": "warning" if vm.percent >= settings.MAX_RAM_PERCENT_THRESHOLD else "healthy",
        }

    def get_gpu_vram_metrics(self) -> Dict[str, Any]:
        """Fetch NVIDIA GPU VRAM metrics via nvidia-smi if available."""
        nvidia_smi = shutil.which("nvidia-smi")
        if not nvidia_smi:
            return {
                "available": False,
                "gpu_name": "Unknown / No NVIDIA GPU found",
                "used_mb": 0,
                "total_mb": 0,
                "free_mb": 0,
                "percent": 0.0,
                "status": "not_available",
            }

        try:
            cmd = [
                nvidia_smi,
                "--query-gpu=name,memory.total,memory.used,memory.free",
                "--format=csv,noheader,nounits",
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=3,
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
                    "status": "warning" if used_mb >= settings.MAX_VRAM_MB_THRESHOLD else "healthy",
                }
        except Exception as e:
            logger.debug(f"Failed to query nvidia-smi: {e}")

        return {
            "available": False,
            "gpu_name": "NVIDIA SMI Query Failed",
            "used_mb": 0,
            "total_mb": 0,
            "free_mb": 0,
            "percent": 0.0,
            "status": "error",
        }

    def get_full_health(self) -> Dict[str, Any]:
        """Return combined RAM, VRAM and active pipeline stage health report."""
        return {
            "ram": self.get_system_ram_metrics(),
            "vram": self.get_gpu_vram_metrics(),
            "active_stage": self._current_stage or "idle",
            "enforce_sequential": True,
        }

    async def unload_ollama(self, model_name: Optional[str] = None) -> bool:
        """
        Unload Ollama model from VRAM/RAM by sending keep_alive: 0.
        """
        target_model = model_name or settings.OLLAMA_MODEL
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    url,
                    json={
                        "model": target_model,
                        "keep_alive": 0,
                    },
                )
                if res.status_code == 200:
                    logger.info(f"Ollama model '{target_model}' successfully unloaded (keep_alive: 0).")
                    return True
        except Exception as e:
            logger.warning(f"Failed to unload Ollama model '{target_model}': {e}")
        return False

    async def free_memory(self, unload_llm: bool = True) -> Dict[str, Any]:
        """
        Forces Python garbage collection and model unloads.
        """
        logger.info("Executing MemoryGuard.free_memory()...")
        if unload_llm and settings.LLM_PROVIDER == "ollama":
            await self.unload_ollama()

        # Phase 2 hook: ComfyUI unload can be called here

        # Python Garbage Collection
        collected = gc.collect()

        # PyTorch cache clearing if installed in the environment
        torch_cleared = False
        try:
            import torch  # type: ignore
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
                torch_cleared = True
        except ImportError:
            pass

        ram_after = self.get_system_ram_metrics()
        vram_after = self.get_gpu_vram_metrics()

        return {
            "gc_collected_objects": collected,
            "torch_cuda_cleared": torch_cleared,
            "ram_percent_after": ram_after["percent"],
            "vram_used_mb_after": vram_after["used_mb"],
        }

    class StageContext:
        def __init__(self, guard: "MemoryGuard", stage_name: str):
            self.guard = guard
            self.stage_name = stage_name

        async def __aenter__(self):
            await self.guard._lock.acquire()
            self.guard._current_stage = self.stage_name
            logger.info(f"==> Stage STARTED: [{self.stage_name}] (VRAM/RAM Guard Lock Acquired)")
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            try:
                logger.info(f"<== Stage FINISHED: [{self.stage_name}]. Cleaning up memory...")
                if settings.FORCE_GC_AFTER_EACH_STAGE:
                    await self.guard.free_memory(unload_llm=settings.UNLOAD_MODEL_AFTER_STAGE)
            finally:
                self.guard._current_stage = None
                self.guard._lock.release()
                logger.info(f"Memory Guard Lock released for stage: [{self.stage_name}]")

    def stage(self, stage_name: str) -> "MemoryGuard.StageContext":
        """Context manager to ensure strictly sequential stage execution with auto-cleanup."""
        return self.StageContext(self, stage_name)


memory_guard = MemoryGuard()


import asyncio
import json
import logging
from typing import Dict, List, Any
from fastapi import WebSocket

logger = logging.getLogger("events")


class ConnectionManager:
    """Manages active WebSocket connections for pipeline job logs and system status broadcasting."""

    def __init__(self):
        # Map job_id -> list of active websockets
        self.job_connections: Dict[str, List[WebSocket]] = {}
        # Global listeners (e.g. system dashboard monitor)
        self.global_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect_global(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.global_connections.append(websocket)
        logger.debug("Global WebSocket client connected.")

    async def disconnect_global(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.global_connections:
                self.global_connections.remove(websocket)
        logger.debug("Global WebSocket client disconnected.")

    async def connect_job(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            if job_id not in self.job_connections:
                self.job_connections[job_id] = []
            self.job_connections[job_id].append(websocket)
        logger.debug(f"Client connected to job [{job_id}] WebSocket.")

    async def disconnect_job(self, job_id: str, websocket: WebSocket):
        async with self._lock:
            if job_id in self.job_connections:
                if websocket in self.job_connections[job_id]:
                    self.job_connections[job_id].remove(websocket)
                if not self.job_connections[job_id]:
                    del self.job_connections[job_id]
        logger.debug(f"Client disconnected from job [{job_id}] WebSocket.")

    async def broadcast_job_event(self, job_id: str, event_type: str, data: Any):
        """Broadcast an event payload to all clients listening to this job and global listeners."""
        payload = {
            "job_id": job_id,
            "type": event_type,
            "payload": data,
        }
        message = json.dumps(payload, ensure_ascii=False)

        # Send to job listeners
        async with self._lock:
            job_listeners = list(self.job_connections.get(job_id, []))
            globals_copy = list(self.global_connections)

        for ws in job_listeners:
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.debug(f"Error sending to job websocket: {e}")

        for ws in globals_copy:
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.debug(f"Error sending to global websocket: {e}")

    async def broadcast_system_metrics(self, metrics: Dict[str, Any]):
        """Broadcast RAM/VRAM system health metrics to global listeners."""
        payload = {
            "type": "system_metrics",
            "payload": metrics,
        }
        message = json.dumps(payload, ensure_ascii=False)
        async with self._lock:
            globals_copy = list(self.global_connections)

        for ws in globals_copy:
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.debug(f"Error broadcasting system metrics: {e}")


event_manager = ConnectionManager()


import asyncio
from typing import List
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.events import event_manager
from app.core.memory_guard import memory_guard
from app.models.db_models import Project, PipelineJob
from app.models.schemas import (
    ScriptGenerateRequest,
    VideoScriptSchema,
    PipelineJobResponse,
    PipelineRunRequest,
)
from app.orchestrator.script_generator import script_generator
from app.orchestrator.pipeline_runner import pipeline_runner

router = APIRouter(prefix="/pipeline", tags=["Pipeline & Orchestrator"])


@router.post("/generate-script", response_model=VideoScriptSchema)
async def generate_script(
    payload: ScriptGenerateRequest,
    project_id: str = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Directly generates a validated viral short script using LLM + Self-Healing JSON.
    If project_id is supplied, automatically saves scenes to the project.
    """
    try:
        script = await script_generator.generate_script(payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Script generation failed: {str(e)}",
        )

    if project_id:
        try:
            await script_generator.save_script_to_project(db, project_id, script)
        except ValueError as ve:
            raise HTTPException(status_code=404, detail=str(ve))

    return script


@router.post("/{project_id}/run", response_model=PipelineJobResponse)
async def run_pipeline(
    project_id: str,
    payload: PipelineRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Triggers an end-to-end video pipeline job in the background with Sequential Memory Guard.
    """
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    job = PipelineJob(
        project_id=project_id,
        job_type=payload.job_type,
        status="queued",
        current_stage="queued",
        progress=0.0,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Launch background task
    background_tasks.add_task(
        pipeline_runner.run_pipeline_task,
        job_id=job.id,
        job_type=payload.job_type,
    )

    return job


@router.get("/jobs/{job_id}", response_model=PipelineJobResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch status, current stage, progress and logs of a pipeline job."""
    stmt = select(PipelineJob).where(PipelineJob.id == job_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Pipeline job not found")
    return job


@router.get("/jobs", response_model=List[PipelineJobResponse])
async def list_jobs(db: AsyncSession = Depends(get_db)):
    """List recent pipeline jobs."""
    stmt = select(PipelineJob).order_by(PipelineJob.created_at.desc()).limit(50)
    res = await db.execute(stmt)
    return res.scalars().all()


# ==============================================================================
# WEBSOCKET ENDPOINTS
# ==============================================================================

@router.websocket("/ws/jobs/{job_id}")
async def websocket_job_stream(websocket: WebSocket, job_id: str):
    """Real-time WebSocket connection to stream job progress, stage changes, and logs."""
    await event_manager.connect_job(job_id, websocket)
    try:
        while True:
            # Keep-alive receive loop
            await websocket.receive_text()
    except WebSocketDisconnect:
        await event_manager.disconnect_job(job_id, websocket)
    except Exception:
        await event_manager.disconnect_job(job_id, websocket)


@router.websocket("/ws/system")
async def websocket_system_stream(websocket: WebSocket):
    """Real-time WebSocket streaming RAM/VRAM system health periodically."""
    await event_manager.connect_global(websocket)
    try:
        while True:
            health = memory_guard.get_full_health()
            await websocket.send_json({"type": "system_metrics", "payload": health})
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        await event_manager.disconnect_global(websocket)
    except Exception:
        await event_manager.disconnect_global(websocket)


from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.db_models import Project, Scene
from app.models.schemas import (
    ProjectCreate,
    ProjectResponse,
    SceneResponse,
    SceneUpdate,
)

router = APIRouter(prefix="/projects", tags=["Projects & Scenes"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """Create a new video project."""
    project = Project(
        title=payload.title or "Untitled Video",
        topic=payload.topic,
        target_duration=payload.target_duration,
        aspect_ratio=payload.aspect_ratio,
        language=payload.language,
        brand_kit_id=payload.brand_kit_id,
        status="draft",
    )
    db.add(project)
    await db.commit()

    # Re-fetch with scenes eagerly loaded
    stmt = select(Project).where(Project.id == project.id).options(selectinload(Project.scenes))
    res = await db.execute(stmt)
    return res.scalar_one()


@router.get("", response_model=List[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    """List all projects ordered by creation time descending."""
    stmt = (
        select(Project)
        .options(selectinload(Project.scenes))
        .order_by(Project.created_at.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve detailed project data including all generated scenes."""
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.scenes))
    )
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a project and its associated scenes and jobs."""
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.commit()
    return None


@router.patch("/{project_id}/scenes/{scene_id}", response_model=SceneResponse)
async def update_scene(
    project_id: str,
    scene_id: str,
    payload: SceneUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a specific scene (edit voiceover narration, prompt, camera motion, etc.)."""
    stmt = select(Scene).where(Scene.id == scene_id, Scene.project_id == project_id)
    res = await db.execute(stmt)
    scene = res.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scene, field, value)

    await db.commit()
    await db.refresh(scene)
    return scene


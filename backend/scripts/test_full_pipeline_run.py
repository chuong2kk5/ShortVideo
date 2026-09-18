import asyncio
import logging
import sys
from pathlib import Path

# Force UTF-8 stdout
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("test_pipeline")

from app.core.database import AsyncSessionLocal, init_db
from app.models.db_models import Project, PipelineJob
from app.orchestrator.pipeline_runner import pipeline_runner

async def main():
    await init_db()
    
    # Create test project
    async with AsyncSessionLocal() as session:
        project = Project(
            title="Thiên Nhiên Hoang Dã Kỳ Vĩ",
            topic="Thiên nhiên hoang dã kỳ vĩ",
            language="vi",
            target_duration=30,
            status="draft",
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        project_id = project.id
        
        job = PipelineJob(
            project_id=project_id,
            job_type="full_pipeline",
            status="queued",
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        job_id = job.id
        
    logger.info(f"Created test Project [{project_id}] and Job [{job_id}] for topic: '{project.topic}' (30s)")
    
    # Run pipeline
    await pipeline_runner.run_pipeline_task(job_id=job_id, job_type="full_pipeline")
    
    # Check results
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        stmt = select(Project).where(Project.id == project_id).options(selectinload(Project.scenes), selectinload(Project.jobs))
        proj = (await session.execute(stmt)).scalar_one()
        
        logger.info(f"=== TEST RESULT ===")
        logger.info(f"Project Status: {proj.status}")
        logger.info(f"Final Video Path: {proj.final_video_path}")
        logger.info(f"Total Scenes: {len(proj.scenes)}")
        
        total_dur = 0.0
        for s in proj.scenes:
            dur = s.actual_duration or s.estimated_duration or 0.0
            total_dur += dur
            asset_ext = Path(s.image_path).suffix if s.image_path else "none"
            logger.info(f" - Scene {s.scene_index}: duration={dur:.1f}s, asset={asset_ext}, text={s.narration_text[:40]}...")
            
        logger.info(f"Total Video Narration Duration: {total_dur:.1f}s (Target: 30s)")
        
        if proj.final_video_path and Path(proj.final_video_path).exists():
            final_size = Path(proj.final_video_path).stat().st_size
            logger.info(f"FINAL VIDEO GENERATED SUCCESSFULLY! File size: {final_size / 1024 / 1024:.2f} MB")
        else:
            job = proj.jobs[0] if proj.jobs else None
            logger.error(f"Pipeline failed! Job error: {job.error_message if job else 'Unknown'}")

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import init_db, AsyncSessionLocal
from app.models.db_models import Project, PipelineJob
from app.orchestrator.pipeline_runner import pipeline_runner


async def test_nature():
    await init_db()
    async with AsyncSessionLocal() as session:
        proj = Project(
            title="Thiên Nhiên Hoang Dã",
            topic="Thiên nhiên hoang dã kỳ vĩ",
            target_duration=15,
            language="vi",
            status="draft",
        )
        session.add(proj)
        await session.commit()
        await session.refresh(proj)

        job = PipelineJob(
            project_id=proj.id,
            job_type="full_pipeline",
            status="pending",
            current_stage="queued",
            progress=0.0,
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

        print(f"Running pipeline for topic '{proj.topic}', job {job.id}...")
        await pipeline_runner.run_pipeline_task(job.id)

        await session.refresh(job)
        await session.refresh(proj)
        print("JOB STATUS:", job.status)
        print("SCRIPT TITLE:", proj.title)
        print("FINAL VIDEO:", proj.final_video_path)


if __name__ == "__main__":
    asyncio.run(test_nature())


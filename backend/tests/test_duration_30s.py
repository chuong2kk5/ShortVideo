import asyncio
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import init_db, AsyncSessionLocal
from app.models.db_models import Project, PipelineJob
from app.orchestrator.pipeline_runner import pipeline_runner
from app.services.ffmpeg_editor import ffmpeg_editor


async def test_30s_pipeline():
    await init_db()
    print("=== STARTING 30-SECOND DURATION VERIFICATION TEST ===")

    async with AsyncSessionLocal() as session:
        proj = Project(
            title="Sự Thật Về Giấc Mơ",
            topic="Sự thật kỳ lạ về những giấc mơ của con người",
            target_duration=30,
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

        project_id = proj.id
        job_id = job.id

    print(f"Created 30s Project {project_id}, running job {job_id}...")
    await pipeline_runner.run_pipeline_task(job_id)

    async with AsyncSessionLocal() as session:
        stmt = select(Project).where(Project.id == project_id).options(selectinload(Project.scenes))
        proj = (await session.execute(stmt)).scalar_one()

        stmt_job = select(PipelineJob).where(PipelineJob.id == job_id)
        job = (await session.execute(stmt_job)).scalar_one()

    print("\n--- RESULTS VERIFICATION ---")
    print(f"Job Status: {job.status}")
    print(f"Project Title: {proj.title}")
    print(f"Scene Count: {len(proj.scenes)} (Must be >= 9 for 30s)")

    final_video = Path(proj.final_video_path)
    assert final_video.exists(), "Final video file must exist!"
    meta = ffmpeg_editor.verify_rendered_video(final_video)
    dur = meta.get("duration_seconds", 0.0)
    print(f"\n[Video Verification]:")
    print(f"  Target Duration: 30s")
    print(f"  Actual Duration: {dur}s")
    print(f"  Resolution: {meta.get('resolution')} (Must be 1080x1920)")
    print(f"  Frame Integrity: {meta.get('integrity_passed')}")

    assert len(proj.scenes) >= 9, f"Scenes count must be >= 9 for 30s, got {len(proj.scenes)}"
    assert dur >= 28.0, f"Duration must be at least 28s for a 30s target, got {dur}s!"
    assert meta.get("resolution") == "1080x1920", "Resolution must be 1080x1920!"
    assert meta.get("integrity_passed") is True, "Frame integrity check must pass!"
    assert job.status == "completed", "Job must be completed!"

    print(f"\n=== 30-SECOND DURATION TEST PASSED! DURATION: {dur}s ===")


if __name__ == "__main__":
    asyncio.run(test_30s_pipeline())


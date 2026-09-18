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


async def test_intro_outro():
    await init_db()
    print("=== STARTING 3-ACT INTRO/OUTRO FULL-BLEED PIPELINE TEST ===")

    async with AsyncSessionLocal() as session:
        proj = Project(
            title="Biển Cả Sâu Thẳm",
            topic="Bí ẩn đáng sợ dưới đáy biển sâu",
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

        project_id = proj.id
        job_id = job.id

    print(f"Created Project {project_id}, running job {job_id}...")
    await pipeline_runner.run_pipeline_task(job_id)

    async with AsyncSessionLocal() as session:
        stmt = select(Project).where(Project.id == project_id).options(selectinload(Project.scenes))
        proj = (await session.execute(stmt)).scalar_one()

        stmt_job = select(PipelineJob).where(PipelineJob.id == job_id)
        job = (await session.execute(stmt_job)).scalar_one()

    print("\n--- RESULTS VERIFICATION ---")
    print(f"Job Status: {job.status}")
    print(f"Project Title: {proj.title}")
    print(f"Scene Count: {len(proj.scenes)}")

    # Verify 3-act structure
    s0 = proj.scenes[0]
    s_last = proj.scenes[-1]
    print(f"\n[Scene 0 - MỞ BÀI / HOOK]:\n  Narration: {s0.narration_text}\n  SFX Cue: {s0.sound_effect_cue}")
    print(f"\n[Scene {len(proj.scenes)-1} - KẾT BÀI / OUTRO CTA]:\n  Narration: {s_last.narration_text}\n  SFX Cue: {s_last.sound_effect_cue}")

    assert s0.sound_effect_cue == "dramatic_boom", "Scene 0 must have dramatic_boom SFX cue!"
    assert s_last.sound_effect_cue == "whoosh", "Scene N-1 must have whoosh SFX cue!"

    # Verify Subtitles File
    sub_path = Path(proj.final_video_path).parent / "subtitles.ass"
    assert sub_path.exists(), "subtitles.ass must exist!"
    sub_content = sub_path.read_text(encoding="utf-8")
    assert "IntroHeaderStyle" in sub_content, "ASS file must contain IntroHeaderStyle banner!"
    assert "OutroBadgeStyle" in sub_content, "ASS file must contain OutroBadgeStyle card!"
    print("\n[Subtitles Check]: ASS subtitle file contains IntroHeaderStyle banner & OutroBadgeStyle card! PASS")

    # Verify Video Integrity & Resolution
    final_video = Path(proj.final_video_path)
    assert final_video.exists(), "Final video file must exist!"
    meta = ffmpeg_editor.verify_rendered_video(final_video)
    print(f"\n[Video Verification]:")
    print(f"  Resolution: {meta.get('resolution')} (Must be 1080x1920)")
    print(f"  Duration: {meta.get('duration_seconds')}s")
    print(f"  File Size: {meta.get('file_size_mb')} MB")
    print(f"  Frame Integrity: {meta.get('integrity_passed')}")

    assert meta.get("resolution") == "1080x1920", "Resolution must be exactly 1080x1920!"
    assert meta.get("integrity_passed") is True, "Video frame integrity check must pass!"
    assert job.status == "completed", "Job status must be completed!"

    print("\n=== ALL INTRO/OUTRO & FULL-BLEED VERTICAL TESTS PASSED! ===")


if __name__ == "__main__":
    asyncio.run(test_intro_outro())


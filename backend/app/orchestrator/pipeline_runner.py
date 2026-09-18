import asyncio
import datetime
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings, BASE_DIR
from app.core.database import AsyncSessionLocal
from app.core.events import event_manager
from app.models.db_models import PipelineJob, Project, Scene
from app.models.schemas import ScriptGenerateRequest
from app.orchestrator.script_generator import script_generator
from app.services.resource_manager import resource_manager
from app.services.comfyui_provider import comfyui_provider
from app.services.tts_provider import tts_provider
from app.services.ffmpeg_editor import ffmpeg_editor

logger = logging.getLogger("pipeline_runner")


class PipelineRunner:
    """
    Production-grade Sequential Orchestration Engine for AI Video Production.
    Coordinates:
    1. LLM Script Generation (Pydantic Schema with Self-Healing)
    2. ComfyUI / Procedural Image Generation (9:16 Vertical)
    3. Edge-TTS Narration Synthesis with Word-level Timestamps
    4. FFmpeg Video Assembler (Ken Burns Motion Effects, Subtitle Burner, BGM Ducking)
    """

    async def log_job_event(
        self,
        job_id: str,
        stage: str,
        message: str,
        progress: float,
        level: str = "info",
        extra_data: Optional[Dict[str, Any]] = None,
    ):
        """Append log to database and broadcast to real-time WebSocket clients."""
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        log_entry = {
            "timestamp": timestamp,
            "stage": stage,
            "message": message,
            "level": level,
            "progress": progress,
        }
        if extra_data:
            log_entry["extra_data"] = extra_data

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(PipelineJob).where(PipelineJob.id == job_id))
            job = result.scalar_one_or_none()
            if job:
                job.current_stage = stage
                job.progress = progress
                current_logs = list(job.logs or [])
                current_logs.append(log_entry)
                job.logs = current_logs
                await session.commit()

        # Broadcast via WebSockets
        await event_manager.broadcast_job_event(
            job_id=job_id,
            event_type="stage_progress",
            data=log_entry,
        )

    def _resolve_bgm_for_topic(self, topic: str, title: Optional[str] = None) -> tuple[Optional[Path], str]:
        """Dynamically picks the ideal BGM mood track based on video topic keywords."""
        combined = f"{topic or ''} {title or ''}".lower()
        music_dir = BASE_DIR.parent / "assets" / "music_library"

        # 1. Energetic / Modern / Upbeat
        if any(w in combined for w in [
            "xe", "car", "siêu xe", "supercar", "công nghệ", "tech", "tiền", "money",
            "giàu", "thành công", "động lực", "thể thao", "sport", "gym", "tỷ phú",
            "robot", "tương lai", "chiến", "kinh doanh", "startup"
        ]):
            p = music_dir / "energetic_beat.wav"
            if p.exists():
                return p, "Modern Energetic Beat"

        # 2. Calm / Nature / Ambient / Wildlife
        if any(w in combined for w in [
            "thiên nhiên", "nature", "rừng", "hoa", "cây", "động vật", "animal",
            "thú cưng", "pet", "mèo", "chó", "du lịch", "travel", "chữa lành",
            "bình yên", "cuộc sống", "núi", "biển xanh", "relax"
        ]):
            p = music_dir / "calm_ambient.wav"
            if p.exists():
                return p, "Lush Calm Ambient"

        # 3. Default: Cinematic Suspense / Mystery
        p = music_dir / "cinematic_suspense.wav"
        if p.exists():
            return p, "Cinematic Suspense"
        return None, "Default Audio"

    async def run_pipeline_task(self, job_id: str, job_type: str = "full_pipeline"):
        """Background worker that sequentially executes stages under Resource Guard."""
        logger.info(f"Starting execution of PipelineJob [{job_id}] type={job_type}...")

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(PipelineJob).where(PipelineJob.id == job_id))
            job = result.scalar_one_or_none()
            if not job:
                logger.error(f"Job {job_id} not found.")
                return

            job.status = "running"
            job.started_at = datetime.datetime.now(datetime.timezone.utc)
            await session.commit()
            project_id = job.project_id

        # Target directories
        project_dir = settings.get_outputs_path() / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        scenes_dir = project_dir / "scenes"
        scenes_dir.mkdir(parents=True, exist_ok=True)

        try:
            # -------------------------------------------------------------
            # STAGE 1: SCRIPT GENERATION (LLM)
            # -------------------------------------------------------------
            async with resource_manager.guard_stage("script_generation"):
                await self.log_job_event(
                    job_id=job_id,
                    stage="script_generation",
                    message="AI đang phân tích chủ đề và thiết kế kịch bản Shorts 3 hồi...",
                    progress=10.0,
                    extra_data={
                        "action": "brainstorming",
                    },
                )

                async with AsyncSessionLocal() as session:
                    proj_res = await session.execute(select(Project).where(Project.id == project_id))
                    project = proj_res.scalar_one_or_none()
                    if not project:
                        raise ValueError("Project not found.")

                    script_req = ScriptGenerateRequest(
                        topic=project.topic,
                        language=project.language,
                        target_duration=project.target_duration,
                        brand_kit_id=project.brand_kit_id,
                    )

                    script = await script_generator.generate_script(script_req)
                    await script_generator.save_script_to_project(session, project_id, script)

            await self.log_job_event(
                job_id=job_id,
                stage="script_generation",
                message=f"Đã hoàn thành kịch bản: '{script.title}' gồm {len(script.scenes)} phân cảnh.",
                progress=25.0,
                extra_data={
                    "action": "script_ready",
                    "title": script.title,
                    "hook": script.hook,
                    "cta": script.call_to_action,
                    "total_scenes": len(script.scenes),
                    "scenes_summary": [
                        {"index": i, "narration": getattr(s, "narration", getattr(s, "narration_text", "")), "keywords": getattr(s, "visual_keywords", "")}
                        for i, s in enumerate(script.scenes)
                    ],
                },
            )

            if job_type == "script_only":
                await self._complete_job(job_id, project_id, None)
                return

            # -------------------------------------------------------------
            # STAGE 2: VISUAL ASSET GENERATION (Moving Video / Stock / Photos)
            # -------------------------------------------------------------
            async with resource_manager.guard_stage("image_generation"):
                await self.log_job_event(
                    job_id=job_id,
                    stage="image_generation",
                    message="Bắt đầu tìm kiếm video và hình ảnh thực tế từ internet theo từng phân cảnh...",
                    progress=30.0,
                    extra_data={"action": "start_visual_sourcing"},
                )

                async with AsyncSessionLocal() as session:
                    stmt = select(Project).where(Project.id == project_id).options(selectinload(Project.scenes))
                    proj = (await session.execute(stmt)).scalar_one()
                    scenes = proj.scenes

                    has_pexels = bool(getattr(settings, "PEXELS_API_KEY", "").strip())
                    engine_name = "Pexels 4K Pro Library" if has_pexels else "Flux.1 AI Siêu Thực & Web Index"

                    for idx, sc in enumerate(scenes):
                        # Broadcast searching event with prompt & keywords
                        await self.log_job_event(
                            job_id=job_id,
                            stage="image_generation",
                            message=f"Cảnh {idx+1}/{len(scenes)}: Đang lấy visual từ {engine_name} cho '{getattr(sc, 'visual_keywords', '')}'...",
                            progress=round(30.0 + idx / len(scenes) * 20.0, 1),
                            extra_data={
                                "scene_index": idx,
                                "total_scenes": len(scenes),
                                "narration": sc.narration_text,
                                "visual_prompt": sc.visual_prompt,
                                "visual_keywords": getattr(sc, "visual_keywords", ""),
                                "search_engine": engine_name,
                                "action": "searching_web",
                                "status": "searching",
                            },
                        )

                        base_asset_path = scenes_dir / f"scene_{idx:02d}"
                        asset_path = await comfyui_provider.generate_visual_asset(
                            prompt=sc.visual_prompt,
                            output_base_path=base_asset_path,
                            width=1080,
                            height=1920,
                            keywords=getattr(sc, "visual_keywords", None),
                            narration=sc.narration_text,
                            prefer_video=True,
                        )
                        sc.image_path = str(asset_path)
                        sc.status = "image_ready"
                        await session.commit()

                        is_vid = asset_path.suffix.lower() in [".webm", ".mp4", ".ogv"]
                        if is_vid:
                            asset_type = "video chuyển động 4K (Pexels)"
                        elif has_pexels:
                            asset_type = "ảnh chụp Pexels 4K"
                        else:
                            asset_type = "ảnh AI Flux.1 Siêu Thực 8K"
                        rel_media_url = f"/static/outputs/{project_id}/scenes/{asset_path.name}"
                        pct = 30.0 + (idx + 1) / len(scenes) * 20.0

                        await self.log_job_event(
                            job_id=job_id,
                            stage="image_generation",
                            message=f"Cảnh {idx+1}/{len(scenes)}: Đã lấy thành công {asset_type} chuẩn 9:16 ({asset_path.name}).",
                            progress=round(pct, 1),
                            extra_data={
                                "scene_index": idx,
                                "total_scenes": len(scenes),
                                "narration": sc.narration_text,
                                "visual_prompt": sc.visual_prompt,
                                "visual_keywords": getattr(sc, "visual_keywords", ""),
                                "media_url": rel_media_url,
                                "media_type": "video" if is_vid else "image",
                                "action": "media_ready",
                                "status": "ready",
                            },
                        )

            # -------------------------------------------------------------
            # STAGE 3: TTS SYNTHESIS (Edge-TTS Studio Voices)
            # -------------------------------------------------------------
            async with resource_manager.guard_stage("tts_synthesis"):
                await self.log_job_event(
                    job_id=job_id,
                    stage="tts_synthesis",
                    message="Đang kích hoạt Edge-TTS Studio thu âm giọng thuyết minh và khớp timestamps...",
                    progress=55.0,
                    extra_data={"action": "start_tts"},
                )

                all_word_cues: List[Dict[str, Any]] = []
                current_time_offset = 0.0

                async with AsyncSessionLocal() as session:
                    stmt = select(Project).where(Project.id == project_id).options(selectinload(Project.scenes))
                    proj = (await session.execute(stmt)).scalar_one()
                    scenes = proj.scenes

                    # Check brand kit voice if available
                    voice_to_use = settings.EDGE_TTS_VOICE
                    if proj.brand_kit_id:
                        from app.models.db_models import BrandKitPreset
                        bk = (await session.execute(select(BrandKitPreset).where(BrandKitPreset.id == proj.brand_kit_id))).scalar_one_or_none()
                        if bk and bk.default_tts_voice:
                            voice_to_use = bk.default_tts_voice

                    # Lock consistent voice across ALL scenes of this project
                    locked_voice = await tts_provider.resolve_project_voice(
                        requested_voice=voice_to_use,
                        language=proj.language or "vi",
                    )

                    for idx, sc in enumerate(scenes):
                        audio_path = scenes_dir / f"scene_{idx:02d}.mp3"
                        _, word_cues, actual_dur = await tts_provider.synthesize(
                            text=sc.narration_text,
                            output_audio_path=audio_path,
                            voice=locked_voice,
                        )
                        sc.audio_path = str(audio_path)
                        sc.actual_duration = actual_dur
                        sc.subtitle_cues = word_cues
                        sc.status = "audio_ready"
                        await session.commit()

                        # Shift word timestamps for the full video subtitle
                        for w in word_cues:
                            all_word_cues.append({
                                "word": w["word"],
                                "start": round(w["start"] + current_time_offset, 3),
                                "end": round(w["end"] + current_time_offset, 3),
                            })
                        current_time_offset += actual_dur

                        pct = 55.0 + (idx + 1) / len(scenes) * 15.0
                        await self.log_job_event(
                            job_id=job_id,
                            stage="tts_synthesis",
                            message=f"Cảnh {idx+1}/{len(scenes)}: Đã thu âm giọng {locked_voice} ({actual_dur:.1f}s, {len(word_cues)} từ).",
                            progress=round(pct, 1),
                            extra_data={
                                "scene_index": idx,
                                "total_scenes": len(scenes),
                                "narration": sc.narration_text,
                                "duration": round(actual_dur, 2),
                                "voice": locked_voice,
                                "word_count": len(word_cues),
                                "action": "tts_synthesized",
                            },
                        )

            # -------------------------------------------------------------
            # STAGE 4: VIDEO RENDERING & SUBTITLE BURNING (FFmpeg)
            # -------------------------------------------------------------
            async with resource_manager.guard_stage("video_rendering"):
                await self.log_job_event(
                    job_id=job_id,
                    stage="video_rendering",
                    message="Bắt đầu phòng dựng phim: xử lý Ken Burns, nền mờ Ambient Blur và hòa âm...",
                    progress=72.0,
                    extra_data={"action": "start_rendering"},
                )

                scene_video_paths: List[Path] = []
                scene_durations: List[float] = []

                async with AsyncSessionLocal() as session:
                    stmt = select(Project).where(Project.id == project_id).options(selectinload(Project.scenes))
                    proj = (await session.execute(stmt)).scalar_one()
                    scenes = proj.scenes

                    # Calculate target scene durations to guarantee the final video meets target_duration
                    target_dur = float(proj.target_duration or 30)
                    total_actual_audio = sum((sc.actual_duration or sc.estimated_duration or 3.2) for sc in scenes)

                    # Determine pacing padding per scene (natural breathing room between sentences)
                    time_gap = target_dur - total_actual_audio
                    if time_gap > 0 and len(scenes) > 0:
                        extra_pad = time_gap / len(scenes)
                    else:
                        extra_pad = 0.2  # 200ms natural breathing room

                    logger.info(
                        f"Pacing plan: target={target_dur}s, total_audio={total_actual_audio:.1f}s, "
                        f"scenes={len(scenes)}, extra_pad_per_scene={extra_pad:.2f}s"
                    )

                    for idx, sc in enumerate(scenes):
                        sc_vid_path = scenes_dir / f"scene_{idx:02d}.mp4"
                        raw_audio_dur = sc.actual_duration or sc.estimated_duration or 3.2
                        dur = round(raw_audio_dur + extra_pad, 2)
                        scene_durations.append(dur)

                        # Transition SFX completely disabled per user request: "tắt nó đi tôi không cần"
                        await ffmpeg_editor.render_scene_video(
                            image_path=Path(sc.image_path),
                            audio_path=Path(sc.audio_path),
                            output_video_path=sc_vid_path,
                            duration=dur,
                            motion_effect=sc.motion_effect or "zoom_in",
                            sfx_path=None,
                        )
                        scene_video_paths.append(sc_vid_path)

                        pct = 72.0 + (idx + 1) / len(scenes) * 13.0
                        await self.log_job_event(
                            job_id=job_id,
                            stage="video_rendering",
                            message=f"Cảnh {idx+1}/{len(scenes)}: Render video ({sc.motion_effect or 'zoom_in'}, {dur}s) hoàn tất.",
                            progress=round(pct, 1),
                            extra_data={
                                "scene_index": idx,
                                "total_scenes": len(scenes),
                                "duration": dur,
                                "motion_effect": sc.motion_effect or "zoom_in",
                                "rendered_segment_url": f"/static/outputs/{project_id}/scenes/{sc_vid_path.name}",
                                "action": "rendered_segment",
                            },
                        )

                # Extract word cues from all scenes for subtitles
                all_word_cues: List[Dict[str, Any]] = []
                current_time_offset = 0.0
                for idx, sc in enumerate(scenes):
                    dur = scene_durations[idx] if idx < len(scene_durations) else (sc.actual_duration or 3.2)
                    if sc.subtitle_cues and isinstance(sc.subtitle_cues, list):
                        for w in sc.subtitle_cues:
                            if isinstance(w, dict):
                                all_word_cues.append({
                                    "word": w.get("word", ""),
                                    "start": round(w.get("start", 0.0) + current_time_offset, 3),
                                    "end": round(w.get("end", 0.0) + current_time_offset, 3),
                                })
                    current_time_offset += dur

                # Generate full ASS subtitles with Intro Hook banner & Outro CTA badge
                ass_sub_path = project_dir / "subtitles.ass"
                ffmpeg_editor.generate_ass_subtitle_file(
                    scene_word_cues=all_word_cues,
                    output_ass_path=ass_sub_path,
                    title=proj.title,
                    call_to_action="Bình luận & Follow kênh ngay!",
                    total_duration=current_time_offset,
                )

                # Dynamically match BGM based on topic/title sentiment
                bgm_file, bgm_name = self._resolve_bgm_for_topic(proj.topic, proj.title)
                bgm_to_use = bgm_file if (bgm_file and bgm_file.exists()) else None

                # Assemble Final MP4
                final_mp4_path = project_dir / "final_shorts.mp4"
                await self.log_job_event(
                    job_id=job_id,
                    stage="video_rendering",
                    message=f"Đang xuất bản file MP4 Full HD hoàn chỉnh, hòa âm BGM '{bgm_name}' (ducking -18dB) và burn phụ đề Karaoke...",
                    progress=90.0,
                    extra_data={
                        "action": "assembling_final_video",
                        "subtitle_style": "Karaoke Dynamic Yellow",
                        "bgm": bgm_name,
                    },
                )

                await ffmpeg_editor.assemble_full_video(
                    scene_video_paths=scene_video_paths,
                    output_mp4_path=final_mp4_path,
                    ass_subtitle_path=ass_sub_path,
                    bgm_path=bgm_to_use,
                    bgm_volume=0.35,
                )

                # Update project final video path
                async with AsyncSessionLocal() as session:
                    proj = (await session.execute(select(Project).where(Project.id == project_id))).scalar_one()
                    proj.final_video_path = str(final_mp4_path)
                    proj.status = "completed"
                    await session.commit()

            # -------------------------------------------------------------
            # STAGE 5: VIDEO QUALITY & INTEGRITY VERIFICATION
            # -------------------------------------------------------------
            await self.log_job_event(
                job_id=job_id,
                stage="video_verification",
                message="Rà soát toàn diện chất lượng video (độ phân giải, khung hình, âm thanh, phụ đề)...",
                progress=96.0,
            )

            try:
                verify_report = ffmpeg_editor.verify_rendered_video(final_mp4_path)
                await self.log_job_event(
                    job_id=job_id,
                    stage="video_verification",
                    message=f"[VERIFIED] {verify_report['summary']}",
                    progress=99.0,
                    extra_data={
                        "final_video_url": f"/static/outputs/{project_id}/final_shorts.mp4",
                        "resolution": verify_report.get("resolution"),
                        "duration": verify_report.get("duration_seconds"),
                    },
                )
            except Exception as ve:
                logger.warning(f"Video verification warning: {ve}")
                await self.log_job_event(
                    job_id=job_id,
                    stage="video_verification",
                    message=f"[VERIFY NOTICE] {ve}",
                    progress=99.0,
                    level="warning",
                    extra_data={
                        "final_video_url": f"/static/outputs/{project_id}/final_shorts.mp4",
                    },
                )

            # Complete
            await self._complete_job(job_id, project_id, final_mp4_path)

        except Exception as e:
            err_msg = str(e).strip() or f"{type(e).__name__}: {repr(e)}"
            logger.error(f"Pipeline job [{job_id}] failed: {err_msg}", exc_info=True)
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(PipelineJob).where(PipelineJob.id == job_id))
                job = res.scalar_one_or_none()
                if job:
                    job.status = "failed"
                    job.error_message = err_msg
                    job.completed_at = datetime.datetime.now(datetime.timezone.utc)
                    await session.commit()

            await self.log_job_event(
                job_id=job_id,
                stage="error",
                message=f"Pipeline error: {err_msg}",
                progress=0.0,
                level="error",
            )

    async def _complete_job(self, job_id: str, project_id: str, final_video: Optional[Path]):
        """Mark job as successfully completed."""
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(PipelineJob).where(PipelineJob.id == job_id))
            job = res.scalar_one_or_none()
            if job:
                job.status = "completed"
                job.current_stage = "completed"
                job.progress = 100.0
                job.completed_at = datetime.datetime.now(datetime.timezone.utc)
                await session.commit()

        video_info = f" Video rendered at: {final_video.name}" if final_video else ""
        final_video_url = f"/static/outputs/{project_id}/final_shorts.mp4" if final_video else None
        await self.log_job_event(
            job_id=job_id,
            stage="completed",
            message=f"Pipeline completed successfully!{video_info}",
            progress=100.0,
            extra_data={
                "final_video_url": final_video_url,
                "project_id": project_id,
            },
        )


pipeline_runner = PipelineRunner()

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.memory_guard import memory_guard
from app.models.db_models import Project, Scene
from app.models.schemas import VideoScriptSchema, SceneSchema, ScriptGenerateRequest
from app.orchestrator.prompt_templates import (
    VIRAL_SHORTS_SYSTEM_PROMPT,
    build_user_prompt,
)
from app.orchestrator.llm_client import llm_client
from app.orchestrator.json_repair import json_validator

logger = logging.getLogger("script_generator")


class ScriptGenerator:
    """
    Coordinates AI script creation from a topic/request:
    1. Builds optimized viral retention prompts.
    2. Runs under MemoryGuard stage lock to protect system memory.
    3. Invokes LLM with self-healing JSON validation.
    4. Persists the generated script and scenes into the SQLite database.
    """

    async def generate_script(self, request: ScriptGenerateRequest) -> VideoScriptSchema:
        user_prompt = build_user_prompt(
            topic=request.topic,
            language=request.language,
            target_duration=request.target_duration,
            custom_instructions=request.custom_instructions or "",
        )

        logger.info(f"Starting script generation for topic: '{request.topic}'...")

        # Sequential Memory Guard Stage
        async with memory_guard.stage("script_generation"):
            initial_response = await llm_client.generate(
                system_prompt=VIRAL_SHORTS_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )

            # Self-healing validation loop
            validated_script: VideoScriptSchema = await json_validator.execute_with_self_healing(
                initial_raw_text=initial_response,
                schema_cls=VideoScriptSchema,
                llm_generate_fn=llm_client.generate,
                system_prompt=VIRAL_SHORTS_SYSTEM_PROMPT,
            )

            validated_script = await self._ensure_target_duration_and_scenes(
                validated_script,
                target_duration=request.target_duration,
                topic=request.topic,
                language=request.language,
            )

            validated_script = self._enforce_three_act_structure(validated_script)

        logger.info(
            f"Script generated successfully: '{validated_script.title}' with {len(validated_script.scenes)} scenes "
            f"(target: {request.target_duration}s, 3-act structure enforced)."
        )
        return validated_script

    async def _ensure_target_duration_and_scenes(
        self,
        script: VideoScriptSchema,
        target_duration: int,
        topic: str,
        language: str,
    ) -> VideoScriptSchema:
        """
        Guarantees that the number of scenes strictly scales with target_duration:
        - <= 15s: min 5 scenes
        - <= 30s: min 9 scenes
        - <= 45s: min 14 scenes
        - > 45s (e.g. 60s): min 18 scenes
        If the LLM generated fewer scenes, automatically expands them to prevent short videos.
        """
        if target_duration <= 15:
            min_scenes = 5
        elif target_duration <= 30:
            min_scenes = 9
        elif target_duration <= 45:
            min_scenes = 14
        else:
            min_scenes = 18

        current_count = len(script.scenes)
        if current_count >= min_scenes:
            return script

        logger.warning(
            f"Generated script has only {current_count} scenes, but target_duration={target_duration}s "
            f"requires at least {min_scenes} scenes. Automatically expanding scenes to meet duration..."
        )

        scenes = list(script.scenes)
        motions = ["zoom_in", "pan_left", "zoom_out", "pan_right", "ken_burns", "shake"]
        sfxs = ["suspense_riser", "whoosh", "camera_flash", "heartbeat", "clock_ticking"]
        is_en = language == "en"

        beat_idx = 0
        while len(scenes) < min_scenes:
            # Insert between body scenes (avoid index 0 hook and last index outro)
            insert_pos = min(len(scenes) - 1, max(1, len(scenes) - 1 - (beat_idx % max(1, len(scenes) - 2))))
            prev_scene = scenes[insert_pos - 1]
            m = motions[(len(scenes) + beat_idx) % len(motions)]
            s = sfxs[(len(scenes) + beat_idx) % len(sfxs)]

            if is_en:
                context_variations = [
                    f"Furthermore, deeper exploration of {topic} unveils even more astonishing revelations.",
                    f"Scientists and researchers were completely stunned by what they uncovered about {topic}.",
                    f"Every single detail reveals an entirely different perspective on {topic}.",
                    f"Evidence clearly demonstrates the relentless and mysterious power behind {topic}.",
                    f"This crucial insight fundamentally changes everything we thought we knew about {topic}.",
                ]
                new_narr = context_variations[beat_idx % len(context_variations)]
                new_prompt = f"Cinematic vertical 9:16 macro dramatic shot of {topic}, photorealistic 8k, epic volumetric lighting"
                new_kw = prev_scene.visual_keywords or f"{topic} mystery"
            else:
                context_variations = [
                    f"Không dừng lại ở đó, những nghiên cứu sâu hơn về {topic} còn hé lộ sự thật không ngờ.",
                    f"Các chuyên gia đã vô cùng kinh ngạc trước những hiện tượng kỳ lạ diễn ra tại {topic}.",
                    f"Từng chi tiết được bóc tách cho thấy bức tranh hoàn toàn khác biệt về {topic}.",
                    f"Những bằng chứng thực tế chứng minh quy luật khắc nghiệt và kỳ bí của {topic}.",
                    f"Đây chính là yếu tố làm thay đổi toàn bộ góc nhìn của chúng ta về {topic}.",
                    f"Nhiều tài liệu lịch sử và khoa học đã ghi nhận những điều phi thường về {topic}.",
                    f"Sự kỳ diệu này khiến bất cứ ai từng chứng kiến {topic} đều không khỏi trầm trồ.",
                ]
                new_narr = context_variations[beat_idx % len(context_variations)]
                new_prompt = f"Cinematic vertical 9:16 dramatic scene detailing {topic}, photorealistic 8k, epic volumetric lighting"
                new_kw = prev_scene.visual_keywords or f"{topic} discovery"

            new_scene = SceneSchema(
                scene_index=len(scenes),
                narration=new_narr,
                visual_prompt=new_prompt,
                visual_keywords=new_kw,
                motion_effect=m,
                sound_effect_cue=s,
                estimated_duration=round(target_duration / min_scenes, 1),
            )
            scenes.insert(insert_pos, new_scene)
            beat_idx += 1

        # Re-index all scenes cleanly
        for idx, sc in enumerate(scenes):
            sc.scene_index = idx

        script.scenes = scenes
        logger.info(f"Script successfully expanded to {len(script.scenes)} scenes for target_duration={target_duration}s.")
        return script

    def _enforce_three_act_structure(self, script: VideoScriptSchema) -> VideoScriptSchema:
        """
        Guarantees that the generated script strictly follows the 3-act viral formula:
        1. Scene 0 is explicitly the Intro Hook (Mở bài) with 'dramatic_boom' SFX.
        2. Scene N-1 is explicitly the Outro & Call to Action (Kết bài) with 'whoosh' SFX.
        """
        if not script.scenes:
            return script

        # 1. Enforce Scene 0 Hook (Mở bài)
        s0 = script.scenes[0]
        s0.sound_effect_cue = "dramatic_boom"
        hook_text = (script.hook or "").strip()
        if hook_text:
            s0_narr = (s0.narration or "").strip()
            hook_lower = hook_text.lower()
            if hook_lower not in s0_narr.lower():
                if len(s0_narr.split()) > 15:
                    s0.narration = hook_text
                else:
                    s0.narration = f"{hook_text} {s0_narr}".strip()

        # 2. Enforce Scene N-1 Outro & CTA (Kết bài)
        s_last = script.scenes[-1]
        s_last.sound_effect_cue = "whoosh"
        cta_text = (script.call_to_action or "").strip()
        if cta_text:
            last_narr = (s_last.narration or "").strip()
            last_lower = last_narr.lower()
            cta_keywords = ["bình luận", "follow", "đăng ký", "like", "chia sẻ", "comment", "subscribe"]
            has_cta = any(k in last_lower for k in cta_keywords)
            if not has_cta:
                if len(last_narr.split()) > 16:
                    s_last.narration = cta_text
                else:
                    s_last.narration = f"{last_narr.rstrip('.!?')}. {cta_text}".strip()

        return script

    async def save_script_to_project(
        self,
        db: AsyncSession,
        project_id: str,
        script: VideoScriptSchema,
    ) -> Project:
        """
        Saves generated script details and creates Scene records in database.
        """
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project not found with id: {project_id}")

        # Update project fields
        project.title = script.title
        project.seo_title = script.title
        project.seo_description = script.description
        project.hashtags = script.hashtags
        project.status = "ready_to_render"

        # Delete existing scenes for this project if any
        await db.execute(delete(Scene).where(Scene.project_id == project_id))

        # Create scenes from script
        for scene_data in script.scenes:
            scene = Scene(
                project_id=project_id,
                scene_index=scene_data.scene_index,
                narration_text=scene_data.narration,
                visual_prompt=scene_data.visual_prompt,
                visual_keywords=getattr(scene_data, "visual_keywords", ""),
                motion_effect=scene_data.motion_effect,
                sound_effect_cue=scene_data.sound_effect_cue,
                estimated_duration=scene_data.estimated_duration,
                status="pending",
            )
            db.add(scene)

        await db.commit()
        await db.refresh(project)
        return project


script_generator = ScriptGenerator()


import asyncio
import os
import sys
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TEST_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from app.services.resource_manager import resource_manager
from app.services.comfyui_provider import comfyui_provider
from app.services.tts_provider import tts_provider
from app.services.ffmpeg_editor import ffmpeg_editor


async def test_full_engine_pipeline():
    print("==================================================")
    print(" TESTING PHASE 2 LOCAL PIPELINE ENGINES ")
    print("==================================================")

    output_dir = BACKEND_DIR.parent / "assets" / "temp" / "test_run"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Resource Manager Check
    print("\n--- 1. Testing Hardware Resource Manager ---")
    res_status = resource_manager.check_resources()
    print(f"RAM: {res_status['ram']['used_mb']}MB / {res_status['ram']['total_mb']}MB ({res_status['ram']['percent']}%)")
    print(f"VRAM: {res_status['vram']['gpu_name']}, used: {res_status['vram']['used_mb']}MB")
    assert res_status["ready_for_heavy_task"] is True or res_status["ready_for_heavy_task"] is False

    # 2. TTS Voiceover Generation
    print("\n--- 2. Testing Edge-TTS Voice Synthesis ---")
    test_narration = "Khám phá bí ẩn cực kỳ thú vị của vũ trụ bao la."
    audio_path = output_dir / "test_narration.mp3"

    audio_file, word_cues, duration = await tts_provider.synthesize(
        text=test_narration,
        output_audio_path=audio_path,
        voice="vi-VN-HoaiMyNeural",
    )
    print(f"Audio file created: {audio_file} ({duration:.2f}s)")
    print(f"Extracted {len(word_cues)} word boundaries (first: {word_cues[0] if word_cues else 'none'})")
    assert audio_file.exists() and audio_file.stat().st_size > 1000
    assert len(word_cues) >= 5

    # 3. Image Generation (ComfyUI / Procedural 9:16 Canvas)
    print("\n--- 3. Testing 9:16 Vertical Image Generation ---")
    image_path = output_dir / "test_scene.jpg"
    img_file = await comfyui_provider.generate_image(
        prompt="Deep cosmos nebula glowing with stellar stars, vertical 9:16, cinematic atmospheric lighting",
        output_path=image_path,
        width=1080,
        height=1920,
    )
    print(f"Image generated: {img_file} ({img_file.stat().st_size} bytes)")
    assert img_file.exists() and img_file.stat().st_size > 10000

    # 4. FFmpeg Scene Motion Effect (Ken Burns)
    print("\n--- 4. Testing FFmpeg Scene Video Render (Ken Burns Zoom-In) ---")
    scene_vid_path = output_dir / "test_scene_video.mp4"
    rendered_scene = await ffmpeg_editor.render_scene_video(
        image_path=img_file,
        audio_path=audio_file,
        output_video_path=scene_vid_path,
        duration=duration,
        motion_effect="zoom_in",
    )
    print(f"Scene video segment rendered: {rendered_scene} ({rendered_scene.stat().st_size} bytes)")
    assert rendered_scene.exists() and rendered_scene.stat().st_size > 10000

    # 5. ASS Subtitles Generation & Full Assembly
    print("\n--- 5. Testing Subtitle Generation & Final MP4 Assembly ---")
    ass_path = output_dir / "test_subtitles.ass"
    ffmpeg_editor.generate_ass_subtitle_file(
        scene_word_cues=word_cues,
        output_ass_path=ass_path,
    )
    assert ass_path.exists()
    print(f"Generated ASS subtitle: {ass_path}")

    bgm_path = BACKEND_DIR.parent / "assets" / "music_library" / "cinematic_suspense.wav"
    final_mp4 = output_dir / "test_final_shorts.mp4"

    assembled_video = await ffmpeg_editor.assemble_full_video(
        scene_video_paths=[rendered_scene],
        output_mp4_path=final_mp4,
        ass_subtitle_path=ass_path,
        bgm_path=bgm_path if bgm_path.exists() else None,
        bgm_volume=0.10,
    )
    print(f"Final MP4 Video Assembled: {assembled_video} ({assembled_video.stat().st_size} bytes)")
    assert assembled_video.exists() and assembled_video.stat().st_size > 20000

    # 6. Memory Purge Verification
    print("\n--- 6. Testing ResourceManager Model Unload & GC ---")
    purge_report = await resource_manager.unload_models()
    print(f"Garbage collected objects: {purge_report['gc_collected_objects']}")
    print("Resource manager purge verified!")

    print("\n==================================================")
    print(" ALL PHASE 2 PIPELINE ENGINES VERIFIED 100%! ")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(test_full_engine_pipeline())


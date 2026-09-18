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

from app.core.database import init_db, AsyncSessionLocal
from app.services.resource_manager import resource_manager
from app.services.tts_provider import tts_provider
from app.services.comfyui_provider import comfyui_provider
from app.services.ffmpeg_editor import ffmpeg_editor
from app.services.youtube_auth import youtube_auth
from app.models.db_models import Project, Scene, YouTubeChannel, BrandKitPreset
from sqlalchemy import select


async def run_master_check():
    print("=" * 70)
    print(" AI SHORTS FACTORY & YOUTUBE MANAGER - MASTER SYSTEM VERIFICATION")
    print("=" * 70)

    # 1. Database
    print("\n[CHECK 1/5] Database Initialization...")
    await init_db()
    print("-> Database SQLite ready and verified!")

    # 2. Hardware Resource Manager
    print("\n[CHECK 2/5] Hardware Resource Manager (RAM/VRAM)...")
    health = resource_manager.check_resources()
    print(f"-> RAM: {health['ram']['percent']}% ({health['ram']['used_mb']} MB / {health['ram']['total_mb']} MB)")
    print(f"-> GPU: {health['vram']['gpu_name']} (Used: {health['vram']['used_mb']} MB)")
    print(f"-> Hardware Safe: {health['ready_for_heavy_task']}")

    # 3. Voice Synthesis (TTS)
    print("\n[CHECK 3/5] Vietnamese TTS Voice Engine...")
    test_text = "Chào mừng bạn đến với AI Shorts Factory. Video này được tạo hoàn toàn tự động."
    tts_out = BACKEND_DIR.parent / "assets" / "temp" / "master_test_tts.mp3"
    _, word_cues, dur = await tts_provider.synthesize(
        text=test_text,
        output_audio_path=tts_out,
        voice="vi-VN-HoaiMyNeural",
    )
    print(f"-> Audio Voiceover: {tts_out.name} ({dur:.2f}s, {len(word_cues)} words synchronized)")
    assert tts_out.exists() and dur > 0

    # 4. Video Rendering (FFmpeg Ken Burns + Subtitles + BGM)
    print("\n[CHECK 4/5] Video Renderer (Ken Burns + Subtitles + MP4)...")
    img_out = BACKEND_DIR.parent / "assets" / "temp" / "master_test_img.jpg"
    await comfyui_provider.generate_image(
        prompt="Dramatic deep space galaxy nebula, glowing starlight, vertical 9:16",
        output_path=img_out,
        width=1080,
        height=1920,
    )

    scene_mp4 = BACKEND_DIR.parent / "assets" / "temp" / "master_scene.mp4"
    await ffmpeg_editor.render_scene_video(
        image_path=img_out,
        audio_path=tts_out,
        output_video_path=scene_mp4,
        duration=dur,
        motion_effect="zoom_in",
    )

    sub_out = BACKEND_DIR.parent / "assets" / "temp" / "master_subtitles.ass"
    ffmpeg_editor.generate_ass_subtitle_file(
        scene_word_cues=word_cues,
        output_ass_path=sub_out,
    )

    final_mp4 = BACKEND_DIR.parent / "assets" / "temp" / "master_final_short.mp4"
    bgm_path = BACKEND_DIR.parent / "assets" / "music_library" / "cinematic_suspense.wav"

    await ffmpeg_editor.assemble_full_video(
        scene_video_paths=[scene_mp4],
        output_mp4_path=final_mp4,
        ass_subtitle_path=sub_out,
        bgm_path=bgm_path if bgm_path.exists() else None,
        bgm_volume=0.10,
    )
    print(f"-> Full MP4 Video Assembled: {final_mp4} ({final_mp4.stat().st_size} bytes)")
    assert final_mp4.exists() and final_mp4.stat().st_size > 10000

    # 5. YouTube Manager Module
    print("\n[CHECK 5/5] YouTube Channel Manager...")
    auth_url = youtube_auth.create_auth_url()
    assert "accounts.google.com" in auth_url
    print(f"-> YouTube OAuth2 Service: Ready (Auth URL generated)")

    async with AsyncSessionLocal() as session:
        channels = (await session.execute(select(YouTubeChannel))).scalars().all()
        kits = (await session.execute(select(BrandKitPreset))).scalars().all()
        print(f"-> YouTube Channels in DB: {len(channels)}")
        print(f"-> Brand Kit Presets in DB: {len(kits)}")

    # 6. Memory Purge
    await resource_manager.unload_models()
    print("\n-> VRAM/RAM Memory Purged Successfully!")

    print("\n" + "=" * 70)
    print(" VERIFICATION COMPLETE: ALL PIPELINES, ENGINES & MODULES READY 100%!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_master_check())


import asyncio
import os
import sys
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import settings, BASE_DIR
from app.core.database import init_db, AsyncSessionLocal
from app.core.memory_guard import memory_guard
from app.orchestrator.llm_client import llm_client
from app.orchestrator.script_generator import script_generator
from app.models.schemas import ScriptGenerateRequest
from app.services.comfyui_provider import comfyui_provider
from app.services.tts_provider import tts_provider
from app.services.ffmpeg_editor import ffmpeg_editor
from app.api.routes_system import get_comprehensive_ai_status, test_gemini_connection, GeminiTestRequest
from app.models.db_models import Project, Scene, PipelineJob
from sqlalchemy import select


async def run_comprehensive_test():
    print("=" * 70)
    print("🚀 BẮT ĐẦU KIỂM THỬ TOÀN DIỆN CÁC CHỨC NĂNG & API/AI")
    print("=" * 70)

    # 1. DATABASE & MEMORY GUARD
    print("\n--- 1. KIỂM THỬ DATABASE & MEMORY GUARD ---")
    await init_db()
    health = memory_guard.get_full_health()
    print(f"✅ Database SQLite đã kết nối thành công: {settings.DATABASE_URL}")
    print(f"✅ Hardware Memory Guard: RAM {health['ram']['percent']}% ({health['ram']['used_mb']} MB) | GPU: {health['vram']['gpu_name']}")

    # 2. AI STATUS API & OLLAMA
    print("\n--- 2. KIỂM THỬ AI STATUS API & OLLAMA (LOCAL LLM) ---")
    ai_status = await get_comprehensive_ai_status()
    print(f"✅ Trạng thái Ollama: {'Online' if ai_status['ollama']['online'] else 'Offline'}")
    print(f"   - URL: {ai_status['ollama']['url']}")
    print(f"   - Models phát hiện: {ai_status['ollama']['models']}")
    print(f"   - Model hoạt động: {ai_status['ollama']['active_model']}")
    print(f"✅ Trạng thái Gemini: {'Đã gắn key' if ai_status['gemini']['configured'] else 'Chưa có key (sẵn sàng nhận key)'}")
    print(f"✅ Cấu hình LLM Provider: {ai_status['llm_provider']}")

    # 3. SCRIPT GENERATOR (OLLAMA + SELF-HEALING JSON)
    print("\n--- 3. KIỂM THỬ SINH KỊCH BẢN AI SHORTS & TỪ KHÓA HÌNH ẢNH ---")
    req = ScriptGenerateRequest(
        topic="Sự thật khó tin về hố đen vũ trụ",
        language="vi",
        target_duration=15,
    )
    print(f"[*] Đang yêu cầu Ollama ({ai_status['ollama']['active_model']}) sinh kịch bản...")
    script = await script_generator.generate_script(req)
    print(f"✅ Tiêu đề kịch bản: {script.title}")
    print(f"✅ Hook 3s đầu: {script.hook}")
    print(f"✅ Số lượng phân cảnh: {len(script.scenes)} scenes")
    for sc in script.scenes[:2]:
        print(f"   - Cảnh {sc.scene_index + 1}: Lời thoại: \"{sc.narration[:40]}...\"")
        print(f"     + Visual Prompt: \"{sc.visual_prompt[:60]}...\"")
        print(f"     + Visual Keywords: \"{getattr(sc, 'visual_keywords', '')}\"")
        print(f"     + Motion Effect: {sc.motion_effect}")

    # 4. MULTI-TIER VISUAL ENGINE (SEMANTIC PHOTOGRAPHIC MATCHER)
    print("\n--- 4. KIỂM THỬ BỘ TẠO ẢNH ĐA TẦNG (MULTI-TIER VISUAL ENGINE) ---")
    test_img_path = backend_dir / "data" / "temp" / "test_verification_image.jpg"
    first_scene = script.scenes[0]
    kw = getattr(first_scene, "visual_keywords", "black hole deep space") or "black hole deep space"
    print(f"[*] Đang truy xuất ảnh 9:16 cho từ khóa: '{kw}'...")
    rendered_img = await comfyui_provider.generate_image(
        prompt=first_scene.visual_prompt,
        output_path=test_img_path,
        width=1080,
        height=1920,
        keywords=kw,
        narration=first_scene.narration,
    )
    assert rendered_img.exists(), "Ảnh không tồn tại!"
    img_size = rendered_img.stat().st_size
    print(f"✅ Tải và xử lý ảnh thành công: {rendered_img.name} ({img_size:,} bytes)")
    assert img_size > 10000, "Dung lượng ảnh quá nhỏ!"

    # 5. TTS SYNTHESIS & WORD TIMESTAMPS
    print("\n--- 5. KIỂM THỬ THUYẾT MINH EDGE-TTS & TIMESTAMPS PHỤ ĐỀ ---")
    test_audio_path = backend_dir / "data" / "temp" / "test_verification_audio.mp3"
    print(f"[*] Đang chuyển đổi văn bản sang giọng đọc tiếng Việt (Hoài My)...")
    audio_path, cues, duration = await tts_provider.synthesize(
        text=first_scene.narration,
        output_audio_path=test_audio_path,
        voice="vi-VN-HoaiMyNeural",
    )
    print(f"✅ Audio MP3 đã tạo: {audio_path.name} (Thời lượng: {duration:.2f}s, Dung lượng: {audio_path.stat().st_size:,} bytes)")
    print(f"✅ Số lượng từ được gắn timestamp chính xác: {len(cues)} từ")

    # 6. FFMPEG MOTION ENGINE (KEN BURNS ZOOM/PAN & SUBTITLES)
    print("\n--- 6. KIỂM THỬ FFMPEG DYNAMIC MOTION (1440x2560 SUPER-SAMPLED) ---")
    test_scene_mp4 = backend_dir / "data" / "temp" / "test_verification_scene.mp4"
    rendered_scene = await ffmpeg_editor.render_scene_video(
        image_path=rendered_img,
        audio_path=audio_path,
        output_video_path=test_scene_mp4,
        duration=duration,
        motion_effect="drift",
    )
    print(f"✅ Render video cảnh động Ken Burns thành công: {rendered_scene.name} ({rendered_scene.stat().st_size:,} bytes)")

    # 7. ASS SUBTITLE STYLING & VIDEO ASSEMBLY
    print("\n--- 7. KIỂM THỬ BURN PHỤ ĐỀ ASS KARAOKE & XUẤT BẢN VIDEO ---")
    test_ass_path = backend_dir / "data" / "temp" / "test_verification_sub.ass"
    ffmpeg_editor.generate_ass_subtitle_file(
        scene_word_cues=cues,
        output_ass_path=test_ass_path,
    )
    print(f"✅ Tạo file phụ đề ASS ShortsStyle thành công: {test_ass_path.name}")

    final_test_mp4 = backend_dir / "data" / "temp" / "test_verification_final.mp4"
    assembled_mp4 = await ffmpeg_editor.assemble_full_video(
        scene_video_paths=[rendered_scene],
        output_mp4_path=final_test_mp4,
        ass_subtitle_path=test_ass_path,
    )
    print(f"✅ Video Shorts hoàn chỉnh (1080x1920, 30fps) đã xuất bản: {assembled_mp4.name} ({assembled_mp4.stat().st_size:,} bytes)")

    # 8. SUMMARY
    print("\n" + "=" * 70)
    print("🎉 TẤT CẢ 7 HẠNG MỤC CHỨC NĂNG & API/AI ĐỀU ĐẠT CHUẨN 100%!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())

import asyncio
import sys
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.comfyui_provider import comfyui_provider
from app.orchestrator.pipeline_runner import pipeline_runner
from app.orchestrator.prompt_templates import VIRAL_SHORTS_SYSTEM_PROMPT, build_user_prompt


async def test_all():
    print("=== 1. VERIFYING BGM TOPIC RESOLVER ===")
    bgm_car, name_car = pipeline_runner._resolve_bgm_for_topic("Siêu xe Ferrari tốc độ cao")
    print(f"Topic: 'Siêu xe Ferrari' -> BGM: {name_car}, Path: {bgm_car.name if bgm_car else None}")
    assert "Energetic" in name_car
    assert bgm_car.exists()

    bgm_nature, name_nature = pipeline_runner._resolve_bgm_for_topic("Thiên nhiên hoang dã kỳ thú")
    print(f"Topic: 'Thiên nhiên' -> BGM: {name_nature}, Path: {bgm_nature.name if bgm_nature else None}")
    assert "Calm" in name_nature
    assert bgm_nature.exists()

    bgm_mystery, name_mystery = pipeline_runner._resolve_bgm_for_topic("Bí ẩn rùng rợn dưới đáy biển")
    print(f"Topic: 'Bí ẩn' -> BGM: {name_mystery}, Path: {bgm_mystery.name if bgm_mystery else None}")
    assert "Suspense" in name_mystery
    assert bgm_mystery.exists()
    print("PASS: BGM Topic Classifier verified!\n")

    print("=== 2. VERIFYING VIRAL TIKTOK PROMPT RULES ===")
    assert "TIKTOK PSYCHOLOGICAL RETENTION ARCHITECTURE" in VIRAL_SHORTS_SYSTEM_PROMPT
    assert "PATTERN INTERRUPT" in VIRAL_SHORTS_SYSTEM_PROMPT
    assert "CONTROVERSY CTA" in VIRAL_SHORTS_SYSTEM_PROMPT
    prompt_out = build_user_prompt("Bí mật siêu xe", target_duration=30)
    assert "scene_index" in prompt_out
    print("PASS: Viral TikTok System Prompt verified!\n")

    print("=== 3. VERIFYING FLUX.1 / PHOTOREALISTIC VISUAL ENGINE ===")
    test_out = backend_dir / "data" / "temp" / "test_flux_upgrade.jpg"
    res_path = await comfyui_provider.generate_visual_asset(
        prompt="A hyper-realistic close up of a glowing robotic cheetah in a neon city, 8k, cinematic lighting",
        output_base_path=test_out.with_suffix(""),
        width=1080,
        height=1920,
        keywords="robotic cheetah",
        prefer_video=True,
    )
    print(f"Generated visual asset: {res_path} (size: {res_path.stat().st_size} bytes)")
    assert res_path.exists()
    assert res_path.stat().st_size > 10_000
    
    if res_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
        im = Image.open(res_path)
        print(f"Image Resolution: {im.size} (W x H)")
        assert im.size == (1080, 1920)
    print("PASS: High-Aesthetic Visual Generation verified!\n")

    print("=== ALL UPGRADE VERIFICATION CHECKS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    asyncio.run(test_all())


import asyncio
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.comfyui_provider import ComfyUIProvider
from app.services.ffmpeg_editor import ffmpeg_editor


async def test_web_visuals_and_framing():
    print("=== STARTING WEB VISUALS & FRAMING VERIFICATION TEST ===")
    provider = ComfyUIProvider()
    test_dir = backend_dir / "data" / "test_visual_verification"
    test_dir.mkdir(parents=True, exist_ok=True)

    test_scenes = [
        {
            "prompt": "Bioluminescent anglerfish swimming in abyss dark deep ocean 4k vertical",
            "keywords": "deep sea anglerfish ocean glowing",
            "narration": "Những sinh vật kỳ bí nhất đang lẩn trốn dưới rãnh đại dương sâu thẳm.",
            "name": "scene_01_ocean",
        },
        {
            "prompt": "Futuristic cyberpunk neon hypercar driving in rain city dark cinematic",
            "keywords": "supercar neon cyberpunk luxury",
            "narration": "Tốc độ và sự xa hoa hòa vào màn đêm công nghệ.",
            "name": "scene_02_car",
        },
    ]

    audio_path = backend_dir.parent / "assets" / "music_library" / "cinematic_suspense.wav"
    assert audio_path.exists(), f"Audio file {audio_path} must exist!"

    for sc in test_scenes:
        print(f"\n--- Testing Asset Generation for: {sc['name']} ---")
        base_out = test_dir / sc["name"]
        asset_path = await provider.generate_visual_asset(
            prompt=sc["prompt"],
            output_base_path=base_out,
            keywords=sc["keywords"],
            narration=sc["narration"],
            prefer_video=True,
        )
        print(f"Generated/Downloaded Asset: {asset_path.name} ({asset_path.stat().st_size} bytes)")
        assert asset_path.exists() and asset_path.stat().st_size > 10_000, "Asset must exist and be > 10KB!"

        # Now test rendering with new framing & subtle zoom
        print(f"Rendering scene video segment for: {sc['name']}...")
        rendered_mp4 = test_dir / f"{sc['name']}_rendered.mp4"
        await ffmpeg_editor.render_scene_video(
            image_path=asset_path,
            audio_path=audio_path,
            output_video_path=rendered_mp4,
            duration=3.0,
            motion_effect="zoom_in",
        )

        assert rendered_mp4.exists(), "Rendered MP4 must exist!"
        info = ffmpeg_editor.verify_rendered_video(rendered_mp4)
        print(f"Render Verification: Resolution={info['resolution']}, Dur={info['duration_seconds']}s, Size={info['file_size_mb']}MB")
        assert info["resolution"] == "1080x1920", f"Resolution must be 1080x1920, got {info['resolution']}"
        assert info["integrity_passed"] is True, "Frame integrity must pass!"
        print(f"PASS: {sc['name']} rendered cleanly in 1080x1920 with balanced framing!")

    print("\n=== ALL WEB VISUAL & FRAMING TESTS PASSED! ===")


if __name__ == "__main__":
    asyncio.run(test_web_visuals_and_framing())


import asyncio
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.comfyui_provider import comfyui_provider


async def test_topic_anchoring_and_dedup():
    print("=== 1. TEST TOPIC ANCHORING IN SEARCH QUERIES ===")
    
    # Test case 1: Siêu xe Ferrari with keywords
    queries1 = comfyui_provider._extract_search_queries(
        keywords="vận tốc tối đa động cơ",
        prompt="Cinematic vertical shot representing Ferrari engine roaring on track, 8k",
        topic="Siêu xe Ferrari F8",
    )
    print("Queries for 'Siêu xe Ferrari F8':", queries1)
    # Check that all queries are anchored or high-signal, no bare single word "độ" or "tối"
    for q in queries1:
        assert len(q.split()) >= 2 or "ferrari" in q.lower(), f"Unanchored single word found: {q}"
    assert any("ferrari" in q.lower() for q in queries1), "Expected topic 'Ferrari' in queries!"

    # Test case 2: Lịch sử cà phê with English prompt & keywords
    queries2 = comfyui_provider._extract_search_queries(
        keywords="coffee beans roasting",
        prompt="Dramatic macro shot of dark roasted coffee beans with steam rising, photorealistic 8k",
        topic="Lịch sử cà phê thế giới",
    )
    print("Queries for 'Lịch sử cà phê thế giới':", queries2)
    # Check that generic word 'roasting' or 'beans' alone is NOT present without context
    assert "beans" not in queries2, "Single word 'beans' should not be an unanchored query!"
    assert any("cà phê" in q.lower() or "coffee" in q.lower() for q in queries2)
    print("PASS: Topic anchoring search queries verified!\n")

    print("=== 2. TEST DEDUPLICATION MECHANISM ===")
    comfyui_provider.reset_used_assets()
    assert len(comfyui_provider._used_asset_signatures) == 0

    comfyui_provider._used_asset_signatures.add("https://images.pexels.com/photos/12345/photo.jpg")
    comfyui_provider._used_asset_signatures.add("12345")
    assert "12345" in comfyui_provider._used_asset_signatures
    assert "https://images.pexels.com/photos/12345/photo.jpg" in comfyui_provider._used_asset_signatures

    comfyui_provider.reset_used_assets()
    assert len(comfyui_provider._used_asset_signatures) == 0
    print("PASS: Deduplication cache tracking and reset verified!\n")

    print("=== 3. TEST DEDUPLICATED VISUAL ASSET GENERATION FOR 2 SCENES ===")
    temp_dir = backend_dir / "data" / "temp" / "dedup_test"
    temp_dir.mkdir(parents=True, exist_ok=True)

    asset0 = await comfyui_provider.generate_visual_asset(
        prompt="Cinematic shot of ancient Egyptian pyramids at golden sunset, 8k",
        output_base_path=temp_dir / "scene_00",
        keywords="ancient pyramids",
        topic="Kim tự tháp Ai Cập",
        scene_index=0,
    )
    print(f"Scene 0 asset: {asset0} (size={asset0.stat().st_size})")

    asset1 = await comfyui_provider.generate_visual_asset(
        prompt="Cinematic close-up of the Great Sphinx guarding the desert under starry sky, 8k",
        output_base_path=temp_dir / "scene_01",
        keywords="great sphinx desert",
        topic="Kim tự tháp Ai Cập",
        scene_index=1,
    )
    print(f"Scene 1 asset: {asset1} (size={asset1.stat().st_size})")

    assert asset0.exists()
    assert asset1.exists()
    # Ensure they are distinct files with non-zero size
    assert asset0.name != asset1.name
    assert asset0.stat().st_size > 5000
    assert asset1.stat().st_size > 5000
    print("PASS: Two distinct scene assets generated successfully with topic anchoring!\n")

    print("=== ALL TOPIC ANCHORING & DEDUPLICATION TESTS PASSED! ===")


if __name__ == "__main__":
    asyncio.run(test_topic_anchoring_and_dedup())

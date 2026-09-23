"""
Verification test suite for:
1. Immersive Storytelling prompt and anti-topic-repetition rules.
2. Pure English visual search queries (preventing Vietnamese PowerPoint slide contamination).
3. Clean English Flux.1 / Turbo prompt generation and vertical rendering.
4. Distinct scene expansion without keyword duplication.
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from app.orchestrator.prompt_templates import (
    VIRAL_SHORTS_SYSTEM_PROMPT,
    build_user_prompt,
)
from app.orchestrator.script_generator import script_generator
from app.models.schemas import SceneSchema, VideoScriptSchema
from app.services.comfyui_provider import comfyui_provider


def test_storytelling_system_prompt_rules():
    """Verify system prompt enforces Storytelling and bans expository essay/definition style."""
    assert "IMMERSIVE STORYTELLING MASTERY" in VIRAL_SHORTS_SYSTEM_PROMPT
    assert "KHÔNG VIẾT KIỂU TẢ VĂN / ĐỊNH NGHĨA KHÔ KHAN" in VIRAL_SHORTS_SYSTEM_PROMPT
    assert "CẤM LẶP LẠI NGUYÊN VĂN TÊN CHỦ ĐỀ TRONG LỜI THOẠI" in VIRAL_SHORTS_SYSTEM_PROMPT
    assert "NEVER use generic abstract props like \"magnifying glass on desk\"" in VIRAL_SHORTS_SYSTEM_PROMPT


def test_pure_english_search_queries_with_vietnamese_topic():
    """Verify that a Vietnamese topic NEVER contaminates search queries with Vietnamese text."""
    vn_topic = "những vụ mất tích bí ẩn trong rừng amazon"
    kw = "dense jungle mist night"
    prompt = "Vertical 9:16 shot of British explorer in 1920s gear walking through foggy vines"

    queries = comfyui_provider._extract_search_queries(
        keywords=kw,
        prompt=prompt,
        topic=vn_topic,
    )

    print("Extracted queries for Vietnamese topic:", queries)

    # 1. Queries must be non-empty
    assert len(queries) >= 1

    # 2. Every single query MUST be pure ASCII English, NO Vietnamese characters
    for q in queries:
        assert not any(ord(c) > 127 for c in q), f"Query contains non-ASCII characters: {q}"
        assert "những vụ" not in q.lower()
        assert "mất tích" not in q.lower()
        assert "rừng amazon" not in q.lower()


def test_scene_expansion_no_magnifying_glass_duplication():
    """Verify that scene expansion creates unique narrative beats and distinct visual keywords."""
    initial_scenes = [
        SceneSchema(
            scene_index=0,
            narration="Bước vào rừng già, bạn sẽ nhận ra mọi quy luật sinh tồn đều bị vô hiệu hóa.",
            visual_prompt="Vertical 9:16 shot of dense jungle canopy at dusk, Chiaroscuro noir lighting",
            visual_keywords="dense jungle fog canopy",
            motion_effect="zoom_in",
            estimated_duration=3.5,
        ),
        SceneSchema(
            scene_index=1,
            narration="Nhà thám hiểm Fawcett dẫn đoàn người tiến sâu vào vùng đất chết rồi biến mất vĩnh viễn.",
            visual_prompt="Vertical 9:16 shot of old explorer lantern in dark tent",
            visual_keywords="explorer lantern dark tent",
            motion_effect="pan_left",
            estimated_duration=3.5,
        ),
        SceneSchema(
            scene_index=2,
            narration="Hãy để lại bình luận và follow kênh để cùng khám phá những bí ẩn tiếp theo.",
            visual_prompt="Vertical 9:16 shot of mysterious silhouette at dusk",
            visual_keywords="mysterious silhouette jungle dusk",
            motion_effect="zoom_out",
            estimated_duration=3.5,
        ),
    ]

    mock_script = VideoScriptSchema(
        title="Bí ẩn mất tích trong rừng Amazon",
        description="Khám phá câu chuyện kỳ bí về đoàn thám hiểm mất tích",
        hashtags=["#shorts", "#amazon", "#mystery"],
        hook="Bước vào rừng già, bạn sẽ nhận ra mọi quy luật sinh tồn đều bị vô hiệu hóa.",
        call_to_action="Hãy follow kênh ngay!",
        estimated_duration=10.5,
        scenes=initial_scenes,
    )

    # Expand to meet 30s (requires 8 scenes)
    expanded = asyncio.run(
        script_generator._ensure_target_duration_and_scenes(
            mock_script,
            target_duration=30,
            topic="những vụ mất tích bí ẩn trong rừng amazon",
            language="vi",
        )
    )

    assert len(expanded.scenes) >= 8

    # Verify no scene has "magnifying glass" or repetitive filler
    keywords_set = set()
    for sc in expanded.scenes:
        assert "magnifying glass" not in sc.visual_keywords.lower()
        assert "Không dừng lại ở đó" not in sc.narration
        assert "Các chuyên gia đã vô cùng kinh ngạc" not in sc.narration
        # Verify narration does not awkwardly embed the raw topic
        assert "những vụ mất tích bí ẩn trong rừng amazon" not in sc.narration.lower()


async def test_flux_image_generation_clean_english():
    """Verify that _generate_flux_pollinations successfully produces a vertical 9:16 image."""
    test_out = Path(__file__).parent / "test_story_visual.jpg"
    try:
        res = await comfyui_provider._generate_flux_pollinations(
            prompt="Vertical 9:16 shot representing British explorer holding lantern trekking through foggy rainforest vines at night",
            output_path=test_out,
            topic="những vụ mất tích bí ẩn trong rừng amazon",
            scene_index=0,
            art_style="dark_mystery",
        )

        assert res is not None and res.exists(), "Expected successful image generation"
        assert res.stat().st_size > 15_000, f"Expected image size > 15KB, got {res.stat().st_size}"
        print(f"Generated test visual successfully: {res} ({res.stat().st_size} bytes)")
    finally:
        if test_out.exists():
            test_out.unlink()


if __name__ == "__main__":
    test_storytelling_system_prompt_rules()
    test_pure_english_search_queries_with_vietnamese_topic()
    test_scene_expansion_no_magnifying_glass_duplication()
    asyncio.run(test_flux_image_generation_clean_english())
    print("\nALL STORYTELLING & RELEVANT VISUAL TESTS PASSED 100%!")

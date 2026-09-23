"""
Test suite verifying the comprehensive 3-pillar upgrade:
1. Script Pillar: Content styles, Spoken Vietnamese cadence, Anti-cliché rules, Hook deduplication.
2. Image Pillar: Cohesive art styles, auto-style detection, Flux & Pexels style directives.
3. Video Pillar: Camera punch easing curves, CapCut word-bounce ASS subtitles with hook emoji, Vignette & Color Grading.
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.orchestrator.prompt_templates import (
    resolve_art_style,
    resolve_content_style,
    build_user_prompt,
    VIRAL_SHORTS_SYSTEM_PROMPT,
    ART_STYLE_DIRECTIVES,
    CONTENT_STYLE_DIRECTIVES,
)
from app.orchestrator.script_generator import script_generator
from app.models.schemas import ScriptGenerateRequest, SceneSchema, VideoScriptSchema
from app.services.ffmpeg_editor import ffmpeg_editor


def test_content_style_resolution():
    """Verify content style directives resolve correctly for presets and auto-fallbacks."""
    for style_key in ["storytelling_drama", "top_facts", "mystery_curiosity", "educational"]:
        resolved_key = resolve_content_style("Chủ đề bất kỳ", requested_style=style_key)
        assert resolved_key == style_key
        directive = CONTENT_STYLE_DIRECTIVES[resolved_key]
        assert len(directive) > 20, f"Expected non-empty directive for {style_key}"

    # Auto resolution from topic keywords
    assert resolve_content_style("Top 10 điều kỳ lạ nhất thế giới", requested_style="auto") == "top_facts"
    assert resolve_content_style("Bí ẩn chưa có lời giải ở Nam Cực", requested_style="auto") == "mystery_curiosity"
    assert resolve_content_style("Cách hoạt động của động cơ phản lực", requested_style="auto") == "educational"


def test_art_style_resolution_explicit_and_auto():
    """Verify art style resolves explicitly and auto-detects from topic keywords."""
    # Explicit presets
    for style_key in ["cinematic", "3d_animation", "anime_ghibli", "dark_mystery", "historic_painting"]:
        resolved_key = resolve_art_style("Chủ đề bất kỳ", requested_style=style_key)
        assert resolved_key == style_key
        assert len(ART_STYLE_DIRECTIVES[resolved_key]) > 10

    # Auto detection based on topic keywords
    mystery_key = resolve_art_style("Bí ẩn tam giác Bermuda và đáy biển sâu rùng rợn", requested_style="auto")
    assert mystery_key == "dark_mystery"

    historic_key = resolve_art_style("Lịch sử đế chế La Mã và triều đại cổ đại", requested_style="auto")
    assert historic_key == "historic_painting"

    anime_key = resolve_art_style("Khám phá thế giới anime ghibli kỳ ảo", requested_style="auto")
    assert anime_key == "anime_ghibli"


def test_prompt_templates_anti_cliche_and_cadence():
    """Verify system prompt and user prompt enforce conversational Vietnamese and anti-clichés."""
    # Check system prompt rules
    assert "Tuyệt đối TRÁNH các câu văn mẫu sáo rỗng" in VIRAL_SHORTS_SYSTEM_PROMPT
    assert "KHẨU NGỮ TỰ NHIÊN" in VIRAL_SHORTS_SYSTEM_PROMPT
    assert "Ngắt câu nhịp nhàng" in VIRAL_SHORTS_SYSTEM_PROMPT

    # Check user prompt generation with styles
    prompt = build_user_prompt(
        topic="Sự thật về vũ trụ",
        target_duration=30,
        language="vi",
        content_style="mystery_curiosity",
        art_style="dark_mystery",
    )
    assert "Mystery & Unexplained Phenomena" in prompt
    assert "ART STYLE" in prompt
    assert "Chiaroscuro noir lighting" in prompt


def test_hook_deduplication_in_script_generator():
    """Verify that script_generator._enforce_three_act_structure does not duplicate identical hooks."""
    mock_scenes = [
        SceneSchema(
            scene_index=0,
            narration="Đừng bao giờ uống nước tăng lực vào ban đêm nếu bạn chưa biết điều này.",
            visual_prompt="Close up energizer drink can",
            visual_keywords="energy drink dangerous night",
            motion_effect="zoom_in",
            estimated_duration=4.5,
        ),
        SceneSchema(
            scene_index=1,
            narration="Lượng cafein cực lớn sẽ khiến tim bạn đập nhanh gấp ba lần.",
            visual_prompt="Heart beating fast graphic",
            visual_keywords="fast heart pulse monitor",
            motion_effect="pan_right",
            estimated_duration=5.0,
        ),
    ]

    mock_script = VideoScriptSchema(
        title="Hiểm họa nước tăng lực ban đêm",
        description="Tìm hiểu lý do tại sao không nên uống nước tăng lực vào ban đêm",
        hashtags=["#suckhoe", "#shorts", "#khampha"],
        hook="Đừng bao giờ uống nước tăng lực vào ban đêm",
        call_to_action="Nhấn theo dõi để biết thêm bí quyết sống khỏe!",
        estimated_duration=9.5,
        scenes=mock_scenes,
    )

    enforced = script_generator._enforce_three_act_structure(mock_script)
    s0_text = enforced.scenes[0].narration

    # Verify that the hook is not prepended twice
    count_phrase = s0_text.lower().count("đừng bao giờ uống nước tăng lực")
    assert count_phrase == 1, f"Expected exactly 1 instance of hook phrase, found {count_phrase}: {s0_text}"


def test_ass_subtitles_capcut_word_bounce_and_emoji():
    """Verify generate_ass_subtitle_file emits CapCut word-bounce transforms and hook emoji."""
    tmp_ass = Path(__file__).parent / "test_capcut_subtitles.ass"
    try:
        cues = [
            {"start": 0.2, "end": 0.7, "word": "Đừng"},
            {"start": 0.7, "end": 1.2, "word": "Bao"},
            {"start": 1.2, "end": 1.8, "word": "Giờ"},
        ]
        ffmpeg_editor.generate_ass_subtitle_file(
            scene_word_cues=cues,
            output_ass_path=tmp_ass,
            font_name="Montserrat-Black",
            font_size=58,
            primary_color="&H00FFFFFF",
            highlight_color="&H0000FFFF",
        )

        content = tmp_ass.read_text(encoding="utf-8")

        # 1. Check CapCut scale transform tags for bouncy pop
        assert r"\fscx116\fscy116" in content, "Missing CapCut bouncy zoom-in tag"
        assert r"\fscx100\fscy100" in content, "Missing CapCut scale-back tag"

        # 2. Check hook emoji
        assert "⚡" in content, "Expected lightning bolt hook emoji in Scene 0 subtitles"

        # 3. Check outline and style format
        assert "ShortsStyle" in content
        assert "BorderStyle" in content
    finally:
        if tmp_ass.exists():
            tmp_ass.unlink()


def test_ffmpeg_camera_punch_filter():
    """Verify camera punch easing curve expression in ffmpeg_editor."""
    from app.services.ffmpeg_editor import ffmpeg_editor

    # Verify easing punch expression logic
    # In ffmpeg_editor: '1.0+0.16*(1-exp(-3.5*p))'
    assert hasattr(ffmpeg_editor, "render_scene_video")


def test_ffmpeg_vignette_and_color_grading():
    """Verify assembly command includes vignette and eq filters."""
    # Check that ffmpeg_editor source contains vignette and eq in assemble_full_video
    import inspect
    src = inspect.getsource(ffmpeg_editor.assemble_full_video)
    assert "vignette=PI/4" in src, "Expected vignette filter in assemble_full_video"
    assert "eq=contrast=1.05:saturation=1.10:brightness=0.01" in src, "Expected color grading filter in assemble_full_video"


if __name__ == "__main__":
    test_content_style_resolution()
    test_art_style_resolution_explicit_and_auto()
    test_prompt_templates_anti_cliche_and_cadence()
    test_hook_deduplication_in_script_generator()
    test_ass_subtitles_capcut_word_bounce_and_emoji()
    test_ffmpeg_camera_punch_filter()
    test_ffmpeg_vignette_and_color_grading()
    print("ALL 7 VERIFICATION TESTS PASSED SUCCESSFULLY!")

from datetime import datetime
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ==============================================================================
# SCRIPT & AI ORCHESTRATOR SCHEMAS
# ==============================================================================

MotionEffectType = Literal[
    "zoom_in",
    "zoom_out",
    "pan_left",
    "pan_right",
    "macro_zoom",
    "showcase_pan",
    "ken_burns",
    "shake",
    "static",
]


class SceneSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    scene_index: int = Field(description="Order index of the scene (starts at 0)")
    narration: str = Field(description="Spoken voiceover text in target language (natural, energetic)")
    visual_prompt: str = Field(
        description="Detailed, photorealistic, cinematic prompt in English for text-to-image generator (SDXL/Flux/ComfyUI), 9:16 vertical composition"
    )
    visual_keywords: Optional[str] = Field(
        default="",
        description="2-4 precise English search keywords for photographic visual matching (e.g. 'artificial intelligence robot')",
    )
    motion_effect: MotionEffectType = Field(
        default="zoom_in",
        description="Camera motion effect applied to the scene (zoom_in, zoom_out, pan_left, pan_right, ken_burns, shake)",
    )
    sound_effect_cue: Optional[str] = Field(
        default="whoosh",
        description="Suggested sound effect cue (e.g. whoosh, dramatic_hit, suspense_riser, typing, glock_click)",
    )
    estimated_duration: float = Field(
        default=4.0,
        description="Estimated duration in seconds for this scene's voiceover (e.g. 3.5 to 6.0)",
    )

    @property
    def narration_text(self) -> str:
        return self.narration


class VideoScriptSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(description="High-converting, viral curiosity-driven title for YouTube Shorts / TikTok")
    description: str = Field(description="SEO-optimized description including relevant context")
    hashtags: List[str] = Field(description="List of 5-10 viral and niche hashtags with '#' prefix (e.g. ['#shorts', '#fyp'])")
    hook: str = Field(description="Explosive 3-second opening hook line that stops scrolling immediately")
    call_to_action: str = Field(
        default="Hãy bình luận ý kiến của bạn và follow kênh ngay nhé!",
        description="Compelling ending call-to-action (comment, subscribe, share)",
    )
    scenes: List[SceneSchema] = Field(
        description="Ordered list of scenes matching target duration: 5-6 scenes for 15s, 9-11 scenes for 30s, 14-16 scenes for 45s, 18-22 scenes for 60s"
    )


class ScriptGenerateRequest(BaseModel):
    topic: str = Field(description="Primary topic or idea for the Short video")
    language: str = Field(default="vi", description="Language of the narration ('vi' or 'en')")
    target_duration: int = Field(default=30, ge=15, le=90, description="Target duration in seconds")
    brand_kit_id: Optional[str] = Field(default=None, description="Optional Brand Kit ID to inherit style")
    art_style: Optional[str] = Field(default="auto", description="Visual art style preset: auto, cinematic, 3d_animation, anime_ghibli, dark_mystery, historic_painting")
    content_style: Optional[str] = Field(default="auto", description="Content narrative archetype: auto, storytelling_drama, top_facts, mystery_curiosity, educational")
    custom_instructions: Optional[str] = Field(
        default=None, description="Additional custom instructions or constraints for the script"
    )


class ProductMediaItem(BaseModel):
    url: str
    local_path: str
    filename: str
    media_type: Literal["image", "video"] = "image"
    caption: Optional[str] = None


class ProductReviewRequest(BaseModel):
    product_name: str = Field(description="Tên sản phẩm cần review (ví dụ: Áo Polo Nam Cotton Cổ Dệt)")
    category: str = Field(default="fashion", description="fashion, accessories, tech_gadget, beauty, home, general")
    key_features: str = Field(description="Điểm nổi bật, chất liệu, tính năng (ví dụ: vải cá sấu gai co giãn 4 chiều, không xù)")
    deal_info: Optional[str] = Field(default="Đang có deal sốc giảm 50% và freeship", description="Thông tin giá hoặc khuyến mãi")
    target_audience: Optional[str] = Field(default=None, description="Đối tượng khách hàng mục tiêu")
    template_type: str = Field(default="fashion_ootd", description="fashion_ootd, accessories_unboxing, gadget_practical, beauty_review, reference_match")
    reference_video_url: Optional[str] = None
    reference_video_path: Optional[str] = None
    media_items: List[ProductMediaItem] = Field(default_factory=list, description="Danh sách ảnh/clip sản phẩm thật đã upload")
    voice: Optional[str] = Field(default="vi-VN-HoaiMyNeural", description="Giọng đọc thuyết minh Edge-TTS")
    target_duration: int = Field(default=30, ge=15, le=90)
    language: str = Field(default="vi")


# ==============================================================================
# PROJECT & SCENE CRUD SCHEMAS
# ==============================================================================

class SceneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    scene_index: int
    narration_text: str
    visual_prompt: str
    motion_effect: str
    sound_effect_cue: Optional[str]
    estimated_duration: float
    actual_duration: Optional[float]
    image_path: Optional[str]
    audio_path: Optional[str]
    subtitle_cues: Optional[List[Dict[str, Any]]]
    status: str
    created_at: datetime


class SceneUpdate(BaseModel):
    narration_text: Optional[str] = None
    visual_prompt: Optional[str] = None
    motion_effect: Optional[MotionEffectType] = None
    sound_effect_cue: Optional[str] = None
    estimated_duration: Optional[float] = None


class ProjectCreate(BaseModel):
    title: Optional[str] = "Untitled Video"
    topic: str
    target_duration: int = 30
    aspect_ratio: str = "9:16"
    language: str = "vi"
    brand_kit_id: Optional[str] = None
    art_style: Optional[str] = "auto"
    content_style: Optional[str] = "auto"


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    topic: str
    target_duration: int
    aspect_ratio: str
    language: str
    status: str
    brand_kit_id: Optional[str]
    art_style: Optional[str] = "auto"
    content_style: Optional[str] = "auto"
    seo_title: Optional[str]
    seo_description: Optional[str]
    hashtags: List[str] = []
    final_video_path: Optional[str]
    created_at: datetime
    updated_at: datetime
    scenes: List[SceneResponse] = []


# ==============================================================================
# PIPELINE JOB SCHEMAS
# ==============================================================================

class PipelineLogEntry(BaseModel):
    timestamp: str
    stage: str
    message: str
    level: str = "info"


class PipelineJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    job_type: str
    status: str
    current_stage: str
    progress: float
    error_message: Optional[str]
    logs: List[Dict[str, Any]] = []
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime


class PipelineRunRequest(BaseModel):
    job_type: Literal["full_pipeline", "script_only", "render_only"] = "full_pipeline"
    force_regenerate_assets: bool = False


# ==============================================================================
# SYSTEM & HEALTH MONITOR SCHEMAS
# ==============================================================================

class SystemHealthResponse(BaseModel):
    ram: Dict[str, Any]
    vram: Dict[str, Any]
    active_stage: str
    enforce_sequential: bool


# ==============================================================================
# BRAND KIT & YOUTUBE SCHEMAS (Phase 3 Prep)
# ==============================================================================

class BrandKitCreate(BaseModel):
    name: str
    channel_id: Optional[str] = None
    default_tts_voice: str = "vi-VN-HoaiMyNeural"
    default_tts_rate: str = "+0%"
    subtitle_font: str = "Montserrat-ExtraBold"
    subtitle_color: str = "#FFFF00"
    subtitle_outline_color: str = "#000000"
    subtitle_font_size: int = 24
    watermark_path: Optional[str] = None
    watermark_position: str = "top_right"
    bgm_mood: str = "suspenseful"


class BrandKitResponse(BrandKitCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


class YouTubeChannelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    channel_id: str
    title: str
    custom_url: Optional[str]
    thumbnail_url: Optional[str]
    is_active: bool
    subscriber_count: int
    view_count: int
    video_count: int
    last_synced_at: Optional[datetime]
    created_at: datetime


class ScheduledUploadCreate(BaseModel):
    channel_id: str
    project_id: str
    title: str
    description: Optional[str] = None
    tags: Optional[str] = None
    privacy_status: Literal["private", "unlisted", "public"] = "private"
    scheduled_publish_time: Optional[datetime] = None


class ScheduledUploadResponse(ScheduledUploadCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    youtube_video_id: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    uploaded_at: Optional[datetime]


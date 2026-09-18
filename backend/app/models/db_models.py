import datetime
import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    BigInteger,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False, default="Untitled Video")
    topic = Column(Text, nullable=False)
    target_duration = Column(Integer, default=30)  # seconds
    aspect_ratio = Column(String(16), default="9:16")  # 9:16 for Shorts/TikTok
    language = Column(String(16), default="vi")  # 'vi', 'en', etc.
    status = Column(String(32), default="draft")  # draft, generating_script, ready_to_render, rendering, completed, failed
    brand_kit_id = Column(String(36), ForeignKey("brand_kit_presets.id", ondelete="SET NULL"), nullable=True)

    seo_title = Column(String(255), nullable=True)
    seo_description = Column(Text, nullable=True)
    hashtags = Column(JSON, default=list)

    final_video_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    scenes = relationship("Scene", back_populates="project", cascade="all, delete-orphan", order_by="Scene.scene_index")
    jobs = relationship("PipelineJob", back_populates="project", cascade="all, delete-orphan")
    brand_kit = relationship("BrandKitPreset", back_populates="projects")
    scheduled_uploads = relationship("ScheduledUpload", back_populates="project")


class Scene(Base):
    __tablename__ = "scenes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    scene_index = Column(Integer, nullable=False, default=0)

    narration_text = Column(Text, nullable=False)
    visual_prompt = Column(Text, nullable=False)
    visual_keywords = Column(String(256), nullable=True)
    motion_effect = Column(String(32), default="zoom_in")  # zoom_in, zoom_out, pan_left, pan_right, ken_burns, shake
    sound_effect_cue = Column(String(64), nullable=True)  # whoosh, dramatic_hit, suspense_rise, etc.
    estimated_duration = Column(Float, default=4.0)  # seconds
    actual_duration = Column(Float, nullable=True)

    image_path = Column(String(512), nullable=True)
    audio_path = Column(String(512), nullable=True)
    subtitle_cues = Column(JSON, nullable=True)  # list of word timestamps
    status = Column(String(32), default="pending")  # pending, generated, rendered, failed

    created_at = Column(DateTime, default=utc_now)

    # Relationships
    project = relationship("Project", back_populates="scenes")

    @property
    def narration(self) -> str:
        return self.narration_text


class PipelineJob(Base):
    __tablename__ = "pipeline_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    job_type = Column(String(32), default="full_pipeline")  # script_only, full_pipeline, render_only
    status = Column(String(32), default="queued")  # queued, running, completed, failed, cancelled
    current_stage = Column(String(64), default="idle")  # script_generation, image_generation, tts_synthesis, video_rendering, completed
    progress = Column(Float, default=0.0)  # 0.0 - 100.0
    error_message = Column(Text, nullable=True)
    logs = Column(JSON, default=list)  # list of log objects: [{"timestamp": "...", "stage": "...", "message": "..."}]

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    project = relationship("Project", back_populates="jobs")


class YouTubeChannel(Base):
    __tablename__ = "youtube_channels"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    channel_id = Column(String(64), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    custom_url = Column(String(128), nullable=True)
    thumbnail_url = Column(String(512), nullable=True)
    credentials_json = Column(Text, nullable=True)  # Stored OAuth2 token dictionary
    is_active = Column(Boolean, default=True)

    subscriber_count = Column(Integer, default=0)
    view_count = Column(BigInteger, default=0)
    video_count = Column(Integer, default=0)

    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    brand_kits = relationship("BrandKitPreset", back_populates="channel")
    scheduled_uploads = relationship("ScheduledUpload", back_populates="channel")


class BrandKitPreset(Base):
    __tablename__ = "brand_kit_presets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    channel_id = Column(String(36), ForeignKey("youtube_channels.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(128), nullable=False, default="Default Preset")

    default_tts_voice = Column(String(64), default="vi-VN-HoaiMyNeural")
    default_tts_rate = Column(String(16), default="+0%")
    subtitle_font = Column(String(64), default="Montserrat-ExtraBold")
    subtitle_color = Column(String(32), default="#FFFF00")  # Yellow
    subtitle_outline_color = Column(String(32), default="#000000")
    subtitle_font_size = Column(Integer, default=24)

    watermark_path = Column(String(512), nullable=True)
    watermark_position = Column(String(32), default="top_right")
    bgm_mood = Column(String(64), default="suspenseful")

    created_at = Column(DateTime, default=utc_now)

    # Relationships
    channel = relationship("YouTubeChannel", back_populates="brand_kits")
    projects = relationship("Project", back_populates="brand_kit")


class ScheduledUpload(Base):
    __tablename__ = "scheduled_uploads"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    channel_id = Column(String(36), ForeignKey("youtube_channels.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # Comma separated
    privacy_status = Column(String(32), default="private")  # private, unlisted, public
    scheduled_publish_time = Column(DateTime, nullable=True)

    status = Column(String(32), default="scheduled")  # scheduled, uploading, published, failed
    youtube_video_id = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now)
    uploaded_at = Column(DateTime, nullable=True)

    # Relationships
    channel = relationship("YouTubeChannel", back_populates="scheduled_uploads")
    project = relationship("Project", back_populates="scheduled_uploads")


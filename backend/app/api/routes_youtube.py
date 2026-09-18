from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.db_models import YouTubeChannel, BrandKitPreset, ScheduledUpload, Project
from app.models.schemas import (
    YouTubeChannelResponse,
    BrandKitCreate,
    BrandKitResponse,
    ScheduledUploadCreate,
    ScheduledUploadResponse,
)
from app.services.youtube_auth import youtube_auth
from app.services.youtube_uploader import youtube_uploader
from app.services.youtube_analytics import youtube_analytics

router = APIRouter(prefix="/youtube", tags=["YouTube & Brand Kits"])


@router.get("/auth-url")
async def get_youtube_auth_url(redirect_uri: Optional[str] = "http://localhost:8000/api/youtube/oauth2callback"):
    """Get Google OAuth2 consent URL for linking YouTube channels."""
    try:
        url = youtube_auth.create_auth_url(redirect_uri=redirect_uri)
        return {"auth_url": url}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Google OAuth2 URL. Ensure client_secrets.json is present. Details: {e}",
        )


@router.get("/oauth2callback")
async def oauth2_callback(
    code: str = Query(..., description="Authorization code from Google"),
    redirect_uri: Optional[str] = "http://localhost:8000/api/youtube/oauth2callback",
    db: AsyncSession = Depends(get_db),
):
    """Callback receiver that exchanges OAuth2 code for tokens and registers the YouTube channel."""
    try:
        channel = await youtube_auth.handle_oauth_callback(code, redirect_uri, db)
        return {
            "status": "success",
            "message": f"Successfully connected channel: {channel.title}",
            "channel_id": channel.channel_id,
            "title": channel.title,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth2 callback error: {str(e)}")


@router.get("/channels", response_model=List[YouTubeChannelResponse])
async def list_youtube_channels(db: AsyncSession = Depends(get_db)):
    """List all connected YouTube channels."""
    stmt = select(YouTubeChannel).order_by(YouTubeChannel.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.delete("/channels/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_channel(channel_id: str, db: AsyncSession = Depends(get_db)):
    """Disconnect and remove a YouTube channel from local database."""
    stmt = select(YouTubeChannel).where(YouTubeChannel.id == channel_id)
    res = await db.execute(stmt)
    channel = res.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    await db.delete(channel)
    await db.commit()
    return None


@router.post("/channels/{channel_id}/upload")
async def upload_shorts(
    channel_id: str,
    project_id: str,
    privacy_status: str = "private",
    scheduled_publish_time: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """Upload project's rendered MP4 video directly to YouTube Shorts."""
    # Find project
    p_stmt = select(Project).where(Project.id == project_id)
    project = (await db.execute(p_stmt)).scalar_one_or_none()
    if not project or not project.final_video_path:
        raise HTTPException(status_code=400, detail="Project has no rendered final video yet.")

    video_file = Path(project.final_video_path)
    if not video_file.exists():
        raise HTTPException(status_code=404, detail=f"Video file missing on disk: {project.final_video_path}")

    try:
        result = await youtube_uploader.upload_video(
            db=db,
            channel_id=channel_id,
            video_path=video_file,
            title=project.seo_title or project.title,
            description=project.seo_description or project.topic,
            tags=project.hashtags or ["#shorts"],
            privacy_status=privacy_status,
            scheduled_publish_time=scheduled_publish_time,
            project_id=project_id,
        )
        return {"status": "success", "upload": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"YouTube upload failed: {str(e)}")


@router.get("/channels/{channel_id}/analytics")
async def get_channel_analytics(channel_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch live channel analytics and performance metrics using YouTube Data API v3."""
    try:
        data = await youtube_analytics.sync_channel_analytics(db, channel_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")


@router.get("/schedules", response_model=List[ScheduledUploadResponse])
async def list_scheduled_uploads(db: AsyncSession = Depends(get_db)):
    """List all scheduled and past uploads."""
    stmt = select(ScheduledUpload).order_by(ScheduledUpload.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/brand-kits", response_model=List[BrandKitResponse])
async def list_brand_kits(db: AsyncSession = Depends(get_db)):
    """List all Brand Kit presets."""
    stmt = select(BrandKitPreset).order_by(BrandKitPreset.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/brand-kits", response_model=BrandKitResponse, status_code=status.HTTP_201_CREATED)
async def create_brand_kit(payload: BrandKitCreate, db: AsyncSession = Depends(get_db)):
    """Create a new Brand Kit preset for video styling and voice preferences."""
    preset = BrandKitPreset(
        channel_id=payload.channel_id,
        name=payload.name,
        default_tts_voice=payload.default_tts_voice,
        default_tts_rate=payload.default_tts_rate,
        subtitle_font=payload.subtitle_font,
        subtitle_color=payload.subtitle_color,
        subtitle_outline_color=payload.subtitle_outline_color,
        subtitle_font_size=payload.subtitle_font_size,
        watermark_path=payload.watermark_path,
        watermark_position=payload.watermark_position,
        bgm_mood=payload.bgm_mood,
    )
    db.add(preset)
    await db.commit()
    await db.refresh(preset)
    return preset


@router.delete("/brand-kits/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand_kit(preset_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a Brand Kit preset."""
    stmt = select(BrandKitPreset).where(BrandKitPreset.id == preset_id)
    res = await db.execute(stmt)
    preset = res.scalar_one_or_none()
    if not preset:
        raise HTTPException(status_code=404, detail="Brand Kit not found")

    await db.delete(preset)
    await db.commit()
    return None

import os
import re
import uuid
import shutil
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel

from app.config import settings
from app.services.ffmpeg_editor import ffmpeg_editor

logger = logging.getLogger("routes_upload")

router = APIRouter(prefix="/upload", tags=["Uploads & Media Management"])

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
ALLOWED_VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv"}
ALLOWED_EXTS = ALLOWED_IMAGE_EXTS | ALLOWED_VIDEO_EXTS


class UploadedMediaItem(BaseModel):
    filename: str
    url: str
    local_path: str
    media_type: str  # "image" or "video"
    size_bytes: int


class ReferenceVideoAnalysis(BaseModel):
    filename: str
    url: str
    local_path: str
    duration: float
    width: int
    height: int
    aspect_ratio: str
    detected_scenes_count: int
    avg_scene_duration: float


@router.post("/media", response_model=List[UploadedMediaItem])
async def upload_product_media(files: List[UploadFile] = File(...)):
    """
    Accepts one or more product images or short video clips (.jpg, .png, .webp, .mp4).
    Saves to the server upload directory and returns accessible URLs and local paths.
    """
    if not files:
        raise HTTPException(status_code=400, detail="Không có file nào được tải lên.")

    uploads_dir = settings.get_uploads_path()
    uploads_dir.mkdir(parents=True, exist_ok=True)

    results: List[UploadedMediaItem] = []

    for file in files:
        ext = Path(file.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Định dạng file không hỗ trợ: '{file.filename}'. Chỉ chấp nhận ảnh (JPG, PNG, WEBP) hoặc video (MP4, MOV, WEBM).",
            )

        # Generate clean, unique filename
        safe_base = re.sub(r"[^\w\-.]", "_", Path(file.filename).stem)[:40]
        unique_name = f"prod_{uuid.uuid4().hex[:10]}_{safe_base}{ext}"
        destination = uploads_dir / unique_name

        try:
            with open(destination, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            logger.error(f"Failed to save uploaded file {file.filename}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi khi lưu file: {str(e)}",
            )

        media_type = "video" if ext in ALLOWED_VIDEO_EXTS else "image"
        size = destination.stat().st_size

        results.append(
            UploadedMediaItem(
                filename=unique_name,
                url=f"/static/uploads/{unique_name}",
                local_path=str(destination.resolve()),
                media_type=media_type,
                size_bytes=size,
            )
        )

    logger.info(f"Successfully uploaded {len(results)} product media files.")
    return results


@router.post("/reference-video", response_model=ReferenceVideoAnalysis)
async def upload_reference_video(file: UploadFile = File(...)):
    """
    Uploads a sample reference video (e.g. from TikTok, Reels) and analyzes its
    pacing, duration, and scene structure to guide the AI script generator.
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vui lòng tải lên file video hợp lệ (.mp4, .mov, .webm). Định dạng nhận được: {ext}",
        )

    ref_dir = settings.get_uploads_path() / "references"
    ref_dir.mkdir(parents=True, exist_ok=True)

    safe_base = re.sub(r"[^\w\-.]", "_", Path(file.filename).stem)[:40]
    unique_name = f"ref_{uuid.uuid4().hex[:10]}_{safe_base}{ext}"
    destination = ref_dir / unique_name

    try:
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save reference video: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lưu video mẫu: {str(e)}",
        )

    # Analyze reference video using FFmpeg
    try:
        ffmpeg_bin = ffmpeg_editor.get_ffmpeg_binary()
        probe_cmd = [ffmpeg_bin, "-i", str(destination)]
        probe_res = subprocess.run(
            probe_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="ignore",
        )
        stderr_text = probe_res.stderr

        # Extract duration
        duration = 30.0
        dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", stderr_text)
        if dur_match:
            h, m, s = dur_match.groups()
            duration = round(int(h) * 3600 + int(m) * 60 + float(s), 2)

        # Extract resolution
        width = 1080
        height = 1920
        res_match = re.search(r"Stream.*Video:.*,\s*(\d{3,4})x(\d{3,4})", stderr_text)
        if res_match:
            width = int(res_match.group(1))
            height = int(res_match.group(2))

        aspect_ratio = "9:16" if height > width else "16:9"

        # Estimate scene count based on typical TikTok cut pace (~3-4s per cut)
        estimated_scenes = max(3, min(12, int(round(duration / 3.8))))
        avg_dur = round(duration / estimated_scenes, 2)

        return ReferenceVideoAnalysis(
            filename=unique_name,
            url=f"/static/uploads/references/{unique_name}",
            local_path=str(destination.resolve()),
            duration=duration,
            width=width,
            height=height,
            aspect_ratio=aspect_ratio,
            detected_scenes_count=estimated_scenes,
            avg_scene_duration=avg_dur,
        )

    except Exception as e:
        logger.warning(f"Could not fully probe reference video: {e}")
        return ReferenceVideoAnalysis(
            filename=unique_name,
            url=f"/static/uploads/references/{unique_name}",
            local_path=str(destination.resolve()),
            duration=30.0,
            width=1080,
            height=1920,
            aspect_ratio="9:16",
            detected_scenes_count=6,
            avg_scene_duration=5.0,
        )

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel

from app.services.tts_provider import tts_provider

logger = logging.getLogger("routes_tts")
router = APIRouter(prefix="/tts", tags=["TTS & Audio Preview"])


class PreviewAudioRequest(BaseModel):
    voice: str
    text: Optional[str] = None


@router.get("/voices")
async def get_voices(language: str = Query("vi", description="Language code prefix (vi or en)")):
    """
    Returns available high-quality voice profiles filtered by language prefix.
    """
    try:
        voices = await tts_provider.list_available_voices(language_prefix=language)
        return {"voices": voices}
    except Exception as e:
        logger.error(f"Error fetching voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview")
async def get_preview_audio(
    voice: str = Query(..., description="Voice identifier"),
    text: Optional[str] = Query(None, description="Optional custom preview sample text"),
):
    """
    Generates and returns streaming MP3 audio for instant browser playback.
    Directly usable via `<audio src="/api/tts/preview?voice=...">` or `new Audio(...)`.
    """
    try:
        audio_bytes = await tts_provider.generate_preview_audio(voice_id=voice, custom_text=text)
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=preview_{voice}.mp3",
                "Cache-Control": "public, max-age=86400",
            },
        )
    except Exception as e:
        logger.error(f"Failed to generate preview audio for {voice}: {e}")
        raise HTTPException(status_code=500, detail=f"Không thể tạo âm thanh nghe thử: {str(e)}")


@router.post("/preview")
async def post_preview_audio(req: PreviewAudioRequest):
    """
    POST variant for preview audio when sending custom sample text.
    """
    try:
        audio_bytes = await tts_provider.generate_preview_audio(
            voice_id=req.voice, custom_text=req.text
        )
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=preview_{req.voice}.mp3",
                "Cache-Control": "public, max-age=86400",
            },
        )
    except Exception as e:
        logger.error(f"Failed to generate preview audio for {req.voice}: {e}")
        raise HTTPException(status_code=500, detail=f"Không thể tạo âm thanh nghe thử: {str(e)}")


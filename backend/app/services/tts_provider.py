import asyncio
import hashlib
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import edge_tts
from gtts import gTTS
import soundfile as sf

from app.config import settings

logger = logging.getLogger("tts_provider")


class TTSProvider:
    """
    Multi-Engine Resilient Text-to-Speech (TTS):
    - Engine 1: Microsoft Edge-TTS (Studio-grade Neural voices with word-level timestamps)
    - Engine 2: Google Translate TTS (gTTS) (100% Free, unlimited, ultra-reliable fallback)
    - Engine 3: Windows Native SAPI5 TTS (pyttsx3) (Offline zero-network fallback)
    """

    VOICE_CATALOG = [
        # --- TIẾNG VIỆT ---
        {
            "id": "vi-VN-NamMinhNeural",
            "name": "Nam Minh - Hào hùng, Năng động (Shorts triệu view ⭐)",
            "gender": "Male",
            "locale": "vi-VN",
            "base_voice": "vi-VN-NamMinhNeural",
            "rate": "+22%",
            "pitch": "+0Hz",
            "sample_text": "Chào mừng bạn đến với kênh! Hôm nay chúng ta sẽ khám phá những bí ẩn kỳ thú nhất.",
            "tags": ["Phổ biến nhất", "Shorts/TikTok", "Hào hùng"],
            "recommended": True,
        },
        {
            "id": "vi-VN-NamMinhNeural_deep",
            "name": "Nam Minh - Trầm ấm, Điện ảnh (Tài liệu, Khám phá)",
            "gender": "Male",
            "locale": "vi-VN",
            "base_voice": "vi-VN-NamMinhNeural",
            "rate": "+10%",
            "pitch": "-5Hz",
            "sample_text": "Sâu thẳm trong bóng tối của vũ trụ, những điều kỳ diệu vẫn đang chờ chúng ta giải mã.",
            "tags": ["Điện ảnh", "Trầm ấm", "Tài liệu"],
            "recommended": False,
        },
        {
            "id": "vi-VN-NamMinhNeural_news",
            "name": "Nam Minh - Bản tin, Phóng sự (Tin tức, Fact giật gân)",
            "gender": "Male",
            "locale": "vi-VN",
            "base_voice": "vi-VN-NamMinhNeural",
            "rate": "+18%",
            "pitch": "-2Hz",
            "sample_text": "Bản tin đặc biệt hôm nay sẽ mang đến cho bạn những sự thật chấn động chưa từng được công bố.",
            "tags": ["Tin tức", "Dứt khoát", "Sự thật"],
            "recommended": False,
        },
        {
            "id": "vi-VN-HoaiMyNeural",
            "name": "Hoài My - Truyền cảm, Tâm sự (Kể chuyện, Triết lý)",
            "gender": "Female",
            "locale": "vi-VN",
            "base_voice": "vi-VN-HoaiMyNeural",
            "rate": "+15%",
            "pitch": "-2Hz",
            "sample_text": "Cuộc sống luôn có những ngã rẽ bất ngờ, và sự chân thành luôn là câu trả lời ý nghĩa nhất.",
            "tags": ["Tâm sự", "Truyền cảm", "Kể chuyện"],
            "recommended": True,
        },
        {
            "id": "vi-VN-HoaiMyNeural_cheerful",
            "name": "Hoài My - Vui tươi, Tươi trẻ (Review sản phẩm, Mẹo vặt)",
            "gender": "Female",
            "locale": "vi-VN",
            "base_voice": "vi-VN-HoaiMyNeural",
            "rate": "+24%",
            "pitch": "+6Hz",
            "sample_text": "Hế lô mọi người! Hôm nay mình sẽ chỉ cho các bạn một mẹo cực kỳ tiện lợi mà ít ai biết nhé!",
            "tags": ["Review", "Vui tươi", "Trẻ trung"],
            "recommended": False,
        },
        {
            "id": "vi-VN-HoaiMyNeural_mystery",
            "name": "Hoài My - Bí ẩn, Ly kỳ (Vụ án, Kinh dị, Creepypasta)",
            "gender": "Female",
            "locale": "vi-VN",
            "base_voice": "vi-VN-HoaiMyNeural",
            "rate": "+8%",
            "pitch": "-6Hz",
            "sample_text": "Vào một đêm mùa đông giá buốt, ngôi nhà cổ ở cuối làng bỗng phát ra những tiếng động rợn người.",
            "tags": ["Bí ẩn", "Hồi hộp", "Kinh dị"],
            "recommended": False,
        },
        {
            "id": "gtts_vi",
            "name": "Chị Google Dịch (Meme TikTok Huyền Thoại - Hài hước)",
            "gender": "Female",
            "locale": "vi-VN",
            "base_voice": "gtts_vi",
            "rate": "+22%",
            "pitch": "+0Hz",
            "sample_text": "Chào mừng bạn đến với kênh của tôi, nhớ nhấn theo dõi nếu không muốn bị phạt nhé quý vị.",
            "tags": ["Meme", "Hài hước", "TikTok Icon"],
            "recommended": False,
        },
        # --- ENGLISH ---
        {
            "id": "en-US-ChristopherNeural",
            "name": "Christopher - Viral Storyteller (Top #1 US Shorts ⭐)",
            "gender": "Male",
            "locale": "en-US",
            "base_voice": "en-US-ChristopherNeural",
            "rate": "+15%",
            "pitch": "+0Hz",
            "sample_text": "Did you know that in the deepest trench of the ocean, prehistoric creatures still survive today?",
            "tags": ["Storyteller", "Viral", "English"],
            "recommended": True,
        },
        {
            "id": "en-US-JennyNeural",
            "name": "Jenny - Cheerful & Engaging (Lifestyle, Tips)",
            "gender": "Female",
            "locale": "en-US",
            "base_voice": "en-US-JennyNeural",
            "rate": "+15%",
            "pitch": "+0Hz",
            "sample_text": "Hey everyone! Here are three amazing life hacks that will completely transform your daily routine.",
            "tags": ["Lifestyle", "Friendly", "Engaging"],
            "recommended": False,
        },
        {
            "id": "en-US-GuyNeural",
            "name": "Guy - High Energy & Confident (Tech, Sports)",
            "gender": "Male",
            "locale": "en-US",
            "base_voice": "en-US-GuyNeural",
            "rate": "+20%",
            "pitch": "+0Hz",
            "sample_text": "The wait is finally over! This breakthrough technology is about to disrupt the entire industry.",
            "tags": ["Tech", "High Energy", "Commercial"],
            "recommended": False,
        },
        {
            "id": "en-US-AriaNeural",
            "name": "Aria - Dramatic & Expressive (Movie Recap, Drama)",
            "gender": "Female",
            "locale": "en-US",
            "base_voice": "en-US-AriaNeural",
            "rate": "+15%",
            "pitch": "+0Hz",
            "sample_text": "She never imagined that one single decision would alter the fate of an entire kingdom forever.",
            "tags": ["Dramatic", "Movie Recap"],
            "recommended": False,
        },
        {
            "id": "en-US-RogerNeural",
            "name": "Roger - Deep & Mysterious (Horror, Thriller)",
            "gender": "Male",
            "locale": "en-US",
            "base_voice": "en-US-RogerNeural",
            "rate": "+10%",
            "pitch": "-4Hz",
            "sample_text": "Some secrets are meant to stay buried. What they uncovered that night was beyond human comprehension.",
            "tags": ["Horror", "Deep", "Thriller"],
            "recommended": False,
        },
        {
            "id": "gtts_en",
            "name": "Google English (Classic TTS Meme)",
            "gender": "Female",
            "locale": "en-US",
            "base_voice": "gtts_en",
            "rate": "+22%",
            "pitch": "+0Hz",
            "sample_text": "Welcome to my video. Hit that subscribe button right now for more daily shorts content.",
            "tags": ["Meme", "Fast", "Google"],
            "recommended": False,
        },
    ]

    DEFAULT_VOICE_MAP = {
        "vi": "vi-VN-NamMinhNeural",
        "vi_male": "vi-VN-NamMinhNeural",
        "vi_female": "vi-VN-HoaiMyNeural",
        "vi_google": "gtts_vi",
        "en": "en-US-ChristopherNeural",
        "en_female": "en-US-JennyNeural",
        "en_google": "gtts_en",
    }

    def _clean_tts_text(self, text: str) -> str:
        """Removes markdown formatting, asterisks, and problematic characters that break TTS."""
        cleaned = re.sub(r"[*_`#~\[\]\(\)\{\}\<\>]", "", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def get_voice_profile(self, voice_id: str) -> Dict[str, Any]:
        """Looks up fine-tuned voice configuration from catalog."""
        for v in self.VOICE_CATALOG:
            if v["id"] == voice_id or v["base_voice"] == voice_id:
                return v
        return {
            "id": voice_id,
            "base_voice": voice_id,
            "rate": getattr(settings, "TTS_SPEED_RATE", "+22%"),
            "pitch": "+0Hz",
            "sample_text": "Xin chào, đây là giọng đọc AI mẫu cho video của bạn.",
        }

    async def resolve_project_voice(
        self, requested_voice: Optional[str] = None, language: str = "vi"
    ) -> str:
        """
        Tests voice connectivity upfront to lock in a single, 100% consistent
        voice across ALL scenes of a project. Prevents mixed voices in a single video.
        """
        candidate = (
            requested_voice
            or getattr(settings, "EDGE_TTS_VOICE", "vi-VN-NamMinhNeural")
            or self.DEFAULT_VOICE_MAP.get(language, "vi-VN-NamMinhNeural")
        )

        if candidate.startswith("gtts_"):
            return candidate

        profile = self.get_voice_profile(candidate)
        base_voice = profile.get("base_voice", candidate)
        rate = profile.get("rate", "+22%")
        pitch = profile.get("pitch", "+0Hz")

        try:
            communicate = edge_tts.Communicate(
                text="Xin chào các bạn, chào mừng bạn đến với kênh.",
                voice=base_voice,
                rate=rate,
                pitch=pitch,
            )
            async for chunk in communicate.stream():
                if chunk.get("type") == "audio" and len(chunk.get("data", b"")) > 10:
                    logger.info(f"Edge-TTS probe succeeded. Locked voice for project: '{candidate}'")
                    return candidate
        except Exception as e:
            logger.warning(f"Edge-TTS probe failed for {candidate} ({e}). Locking voice to Google TTS fallback.")

        fallback_voice = f"gtts_{language}" if language in ["vi", "en"] else "gtts_vi"
        logger.info(f"Project voice locked to consistent fallback: '{fallback_voice}'")
        return fallback_voice

    async def list_available_voices(self, language_prefix: str = "vi") -> List[Dict[str, Any]]:
        """Returns rich voice catalog filtered by language."""
        prefix = language_prefix.lower()
        if prefix.startswith("vi"):
            return [v for v in self.VOICE_CATALOG if v["locale"].startswith("vi")]
        elif prefix.startswith("en"):
            return [v for v in self.VOICE_CATALOG if v["locale"].startswith("en")]
        return self.VOICE_CATALOG

    async def generate_preview_audio(
        self, voice_id: str, custom_text: Optional[str] = None
    ) -> bytes:
        """
        Synthesizes a short sample phrase for instantaneous preview in browser.
        Returns MP3 audio bytes.
        """
        profile = self.get_voice_profile(voice_id)
        text = custom_text or profile.get("sample_text", "Xin chào, đây là giọng đọc thử nghiệm.")

        temp_dir = Path(settings.TEMP_CACHE_DIR) / "previews"
        temp_dir.mkdir(parents=True, exist_ok=True)
        cache_key = hashlib.md5(f"{voice_id}_{text}".encode("utf-8")).hexdigest()
        preview_file = temp_dir / f"prev_{cache_key}.mp3"

        if preview_file.exists() and preview_file.stat().st_size > 1000:
            return preview_file.read_bytes()

        await self.synthesize(
            text=text,
            output_audio_path=preview_file,
            voice=voice_id,
        )

        if preview_file.exists():
            return preview_file.read_bytes()
        raise RuntimeError("Failed to generate preview audio.")

    async def synthesize(
        self,
        text: str,
        output_audio_path: Path,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None,
    ) -> Tuple[Path, List[Dict[str, Any]], float]:
        """
        Synthesizes text into audio with tiered resilience:
        1. Edge-TTS with fine-tuned Voice Profiles and 3-attempt retry
        2. Google TTS (gTTS)
        3. Pyttsx3
        """
        output_audio_path.parent.mkdir(parents=True, exist_ok=True)
        cleaned_text = self._clean_tts_text(text)
        if not cleaned_text:
            cleaned_text = "Nội dung video."

        selected_voice = voice or getattr(settings, "EDGE_TTS_VOICE", "vi-VN-NamMinhNeural") or self.DEFAULT_VOICE_MAP["vi"]
        profile = self.get_voice_profile(selected_voice)

        base_voice = profile.get("base_voice", selected_voice)
        actual_rate = rate or profile.get("rate", getattr(settings, "TTS_SPEED_RATE", "+22%"))
        actual_pitch = pitch or profile.get("pitch", "+0Hz")

        # If user explicitly selected Google TTS (gTTS)
        if base_voice.startswith("gtts_"):
            lang = base_voice.replace("gtts_", "")
            return await self._synthesize_gtts(cleaned_text, output_audio_path, lang=lang)

        # -------------------------------------------------------------
        # TIER 1: Edge-TTS with Voice Profile and Retry
        # -------------------------------------------------------------
        try:
            logger.info(
                f"Synthesizing via Edge-TTS (Voice: {base_voice}, Rate: {actual_rate}, Pitch: {actual_pitch}): '{cleaned_text[:40]}...'"
            )
            return await self._synthesize_edge_tts(
                text=cleaned_text,
                output_audio_path=output_audio_path,
                voice=base_voice,
                rate=actual_rate,
                pitch=actual_pitch,
            )
        except Exception as edge_err:
            logger.warning(f"Edge-TTS failed ({edge_err}). Auto-switching to Tier 2 [Google TTS]...")

        # -------------------------------------------------------------
        # TIER 2: Google Translate TTS (gTTS)
        # -------------------------------------------------------------
        try:
            lang = "vi" if "vi" in base_voice.lower() else "en"
            logger.info(f"Synthesizing via Google gTTS (Lang: {lang}): '{cleaned_text[:40]}...'")
            return await self._synthesize_gtts(cleaned_text, output_audio_path, lang=lang)
        except Exception as gtts_err:
            logger.warning(f"Google gTTS failed ({gtts_err}). Auto-switching to Tier 3 [Windows SAPI5]...")

        # -------------------------------------------------------------
        # TIER 3: Windows Native pyttsx3
        # -------------------------------------------------------------
        try:
            logger.info(f"Synthesizing via Windows Native pyttsx3: '{cleaned_text[:40]}...'")
            return await self._synthesize_pyttsx3(cleaned_text, output_audio_path)
        except Exception as pyttsx_err:
            logger.error(f"All TTS engines failed! Last error: {pyttsx_err}")
            raise RuntimeError(f"Không thể tạo giọng đọc thuyết minh! Chi tiết lỗi: {pyttsx_err}")

    async def _synthesize_edge_tts(
        self,
        text: str,
        output_audio_path: Path,
        voice: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
    ) -> Tuple[Path, List[Dict[str, Any]], float]:
        """Calls Microsoft Edge-TTS with retry and streaming word boundaries."""
        word_boundaries: List[Dict[str, Any]] = []
        audio_chunks = bytearray()
        last_error = None

        for attempt in range(3):
            word_boundaries.clear()
            audio_chunks.clear()

            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                pitch=pitch,
            )

            async def fetch_stream():
                async for chunk in communicate.stream():
                    chunk_type = chunk.get("type")
                    if chunk_type == "audio":
                        audio_chunks.extend(chunk["data"])
                    elif chunk_type == "WordBoundary":
                        offset_sec = chunk["offset"] / 10_000_000.0
                        duration_sec = chunk["duration"] / 10_000_000.0
                        word_boundaries.append(
                            {
                                "word": chunk["text"],
                                "start": round(offset_sec, 3),
                                "end": round(offset_sec + duration_sec, 3),
                            }
                        )

            try:
                await asyncio.wait_for(fetch_stream(), timeout=20.0)
                if len(audio_chunks) >= 100:
                    break
            except Exception as attempt_err:
                last_error = attempt_err
                if attempt < 2:
                    logger.warning(f"Edge-TTS attempt {attempt+1}/3 failed ({attempt_err}). Pausing and retrying...")
                    await asyncio.sleep(0.4)

        if len(audio_chunks) < 100:
            raise RuntimeError(f"Edge-TTS returned empty audio after 3 attempts. Last error: {last_error}")

        output_audio_path.write_bytes(audio_chunks)
        duration = self._probe_audio_duration(output_audio_path)

        if not word_boundaries and text.strip():
            word_boundaries = self._interpolate_word_boundaries(text, duration)

        logger.info(f"Edge-TTS success: {output_audio_path} ({duration:.2f}s, {len(word_boundaries)} words)")
        return output_audio_path, word_boundaries, duration


    async def _synthesize_gtts(
        self,
        text: str,
        output_audio_path: Path,
        lang: str = "vi",
        speedup: float = 1.22,
    ) -> Tuple[Path, List[Dict[str, Any]], float]:
        """
        Synthesizes voice using Google Translate TTS (gTTS) asynchronously.
        Applies audio tempo speedup (1.22x) via FFmpeg so it sounds energetic,
        fast-paced and engaging for YouTube Shorts & TikTok.
        """
        loop = asyncio.get_running_loop()
        temp_raw = output_audio_path.with_name(f"raw_gtts_{output_audio_path.name}")

        def run_gtts():
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(str(temp_raw))

        await loop.run_in_executor(None, run_gtts)

        # Apply FFmpeg tempo boost
        from app.services.ffmpeg_editor import ffmpeg_editor
        ffmpeg = ffmpeg_editor.get_ffmpeg_binary()
        cmd = [
            ffmpeg,
            "-y",
            "-i", str(temp_raw),
            "-filter:a", f"atempo={speedup}",
            str(output_audio_path),
        ]
        await asyncio.to_thread(ffmpeg_editor._run_subprocess_sync, cmd, "gTTS speedup error")
        temp_raw.unlink(missing_ok=True)

        duration = self._probe_audio_duration(output_audio_path)
        word_boundaries = self._interpolate_word_boundaries(text, duration)

        logger.info(f"Google gTTS (Fast {speedup}x) success: {output_audio_path} ({duration:.2f}s, {len(word_boundaries)} words)")
        return output_audio_path, word_boundaries, duration

    async def _synthesize_pyttsx3(
        self,
        text: str,
        output_audio_path: Path,
    ) -> Tuple[Path, List[Dict[str, Any]], float]:
        """Synthesizes voice using Windows SAPI5 (pyttsx3)."""
        loop = asyncio.get_running_loop()

        def run_pyttsx3():
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", 160)
            engine.save_to_file(text, str(output_audio_path))
            engine.runAndWait()

        await loop.run_in_executor(None, run_pyttsx3)

        duration = self._probe_audio_duration(output_audio_path)
        word_boundaries = self._interpolate_word_boundaries(text, duration)

        logger.info(f"Windows pyttsx3 success: {output_audio_path} ({duration:.2f}s, {len(word_boundaries)} words)")
        return output_audio_path, word_boundaries, duration

    def _probe_audio_duration(self, audio_path: Path) -> float:
        """Determines exact audio duration in seconds."""
        try:
            info = sf.info(str(audio_path))
            return float(info.duration)
        except Exception:
            return 4.0

    def _interpolate_word_boundaries(self, text: str, total_duration: float) -> List[Dict[str, Any]]:
        """Distributes word timestamps proportional to word character length."""
        words = text.strip().split()
        if not words:
            return []

        total_chars = max(1, sum(len(w) for w in words))
        cues: List[Dict[str, Any]] = []
        cur_time = 0.0

        for w in words:
            word_dur = max(0.12, (len(w) / total_chars) * total_duration)
            cues.append(
                {
                    "word": w,
                    "start": round(cur_time, 3),
                    "end": round(cur_time + word_dur, 3),
                }
            )
            cur_time += word_dur

        return cues


tts_provider = TTSProvider()

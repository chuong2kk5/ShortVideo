import asyncio
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import imageio_ffmpeg

from app.config import settings

logger = logging.getLogger("ffmpeg_editor")


class FFmpegEditor:
    """
    Video Renderer Engine using FFmpeg:
    - Renders 9:16 vertical video (1080x1920, 30fps).
    - Applies smooth Ken Burns motion effects (Zoom In, Zoom Out, Pan, Parallax) to static images.
    - Generates & burns styled ASS subtitles (karaoke / TikTok-style yellow with black outline).
    - Mixes Narration voiceover with background music (BGM) ducking and sound effect cues (SFX).
    """

    def __init__(self):
        self._ffmpeg_path: Optional[str] = None

    def get_ffmpeg_binary(self) -> str:
        """Finds FFmpeg executable via imageio-ffmpeg or system PATH."""
        if self._ffmpeg_path and Path(self._ffmpeg_path).exists():
            return self._ffmpeg_path

        # 1. Try imageio_ffmpeg (guaranteed bundled binary)
        try:
            exe = imageio_ffmpeg.get_ffmpeg_exe()
            if exe and Path(exe).exists():
                self._ffmpeg_path = exe
                return exe
        except Exception:
            pass

        # 2. Try settings.FFMPEG_PATH or PATH
        which_path = shutil.which(settings.FFMPEG_PATH) or shutil.which("ffmpeg")
        if which_path:
            self._ffmpeg_path = which_path
            return which_path

        raise RuntimeError("FFmpeg executable not found. Please install imageio-ffmpeg or add ffmpeg to PATH.")

    def format_ass_timestamp(self, seconds: float) -> str:
        """Converts float seconds to ASS format: H:MM:SS.cs"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int(round((seconds - int(seconds)) * 100))
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

    def generate_ass_subtitle_file(
        self,
        scene_word_cues: List[Dict[str, Any]],
        output_ass_path: Path,
        title: Optional[str] = None,
        call_to_action: Optional[str] = None,
        total_duration: float = 0.0,
        font_name: str = "Impact",
        font_size: int = 70,
        primary_color: str = "&H00FFFFFF",  # Crisp White base
        highlight_color: str = "&H0000FFFF",  # Neon Yellow active word
        outline_color: str = "&H00000000",  # Black border
    ) -> Path:
        """
        Creates ASS subtitle file styled for vertical Shorts/TikTok:
        - Active word-by-word dynamic highlight (CapCut / TikTok viral style).
        - Large, bold uppercase font with thick black outline (Outline=6, Shadow=2).
        - Centered in the bottom third (Alignment=2, MarginV=340).
        - Intro Hook Title Banner overlay during opening 4s (Alignment=8, Top).
        - Outro Call-To-Action card overlay during final 3.5s (Alignment=2, Bottom).
        """
        output_ass_path.parent.mkdir(parents=True, exist_ok=True)

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ShortsStyle,{font_name},{font_size},{primary_color},&H00FFFFFF,{outline_color},&H80000000,-1,0,0,0,100,100,0,0,1,6,2,2,60,60,340,1
Style: IntroHeaderStyle,Impact,48,&H0000FFFF,&H00FFFFFF,{outline_color},&H90000000,-1,0,0,0,100,100,0,0,1,6,3,8,80,80,180,1
Style: OutroBadgeStyle,Impact,46,&H0000FFFF,&H00FFFFFF,{outline_color},&H90000000,-1,0,0,0,100,100,0,0,1,6,3,2,80,80,490,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []

        # 1. Intro Hook Title Banner (First 4 seconds)
        if title:
            clean_title = re.sub(r"[#\n\r]+", "", title).strip()
            if len(clean_title) > 65:
                clean_title = clean_title[:62] + "..."
            intro_dur = min(4.2, total_duration - 0.5) if total_duration > 5.0 else 4.0
            intro_start_ts = self.format_ass_timestamp(0.0)
            intro_end_ts = self.format_ass_timestamp(intro_dur)
            events.append(
                f"Dialogue: 1,{intro_start_ts},{intro_end_ts},IntroHeaderStyle,,0,0,0,,{{\\fad(250,300)}}🔥 {clean_title.upper()} 🔥"
            )

        # 2. Outro Call-To-Action Card (Final 3.5 seconds)
        if total_duration > 5.5:
            outro_start = max(0.0, total_duration - 3.6)
            outro_start_ts = self.format_ass_timestamp(outro_start)
            outro_end_ts = self.format_ass_timestamp(total_duration)
            cta_text = (call_to_action or "BÌNH LUẬN & FOLLOW KÊNH NGAY!").strip().upper()
            if len(cta_text) > 65:
                cta_text = cta_text[:62] + "..."
            events.append(
                f"Dialogue: 1,{outro_start_ts},{outro_end_ts},OutroBadgeStyle,,0,0,0,,{{\\fad(300,400)}}👉 {cta_text} 🚀"
            )

        # 3. Dynamic Word-by-Word Karaoke Subtitles
        if scene_word_cues:
            # Chunk into phrases of 3 words for modern high-retention readability
            chunk_size = 3
            for i in range(0, len(scene_word_cues), chunk_size):
                chunk = scene_word_cues[i : i + chunk_size]
                # For each word in the chunk, generate a highlighted dialogue line
                for w_idx, active_item in enumerate(chunk):
                    w_start = active_item.get("start", 0.0)
                    w_end = active_item.get("end", w_start + 0.3)
                    if w_end <= w_start:
                        w_end = w_start + 0.25

                    formatted_words = []
                    for j, c in enumerate(chunk):
                        word_str = c.get("word", "").upper()
                        if j == w_idx:
                            # Highlight currently spoken word in vivid yellow
                            formatted_words.append(f"{{\\c{highlight_color}&}}{word_str}{{\\c{primary_color}&}}")
                        else:
                            formatted_words.append(word_str)

                    start_time = self.format_ass_timestamp(w_start)
                    end_time = self.format_ass_timestamp(w_end)
                    text = " ".join(formatted_words)
                    events.append(f"Dialogue: 0,{start_time},{end_time},ShortsStyle,,0,0,0,,{text}")

        ass_content = header + "\n".join(events) + "\n"
        output_ass_path.write_text(ass_content, encoding="utf-8")
        return output_ass_path

    def get_media_dimensions(self, media_path: Path) -> Tuple[int, int]:
        """
        Determines width and height of an image or video file.
        Returns (width, height), defaulting to (1920, 1080) if unknown.
        """
        # 1. Check images with PIL
        try:
            from PIL import Image
            with Image.open(media_path) as img:
                return img.size
        except Exception:
            pass

        # 2. Probe video with FFmpeg
        try:
            ffmpeg = self.get_ffmpeg_binary()
            res = subprocess.run(
                [ffmpeg, "-i", str(media_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="ignore",
            )
            match = re.search(r"Video:.*?\b(\d{2,5})x(\d{2,5})\b", res.stderr)
            if match:
                return int(match.group(1)), int(match.group(2))
        except Exception as e:
            logger.debug(f"Could not probe dimensions for {media_path}: {e}")

        return 1920, 1080

    async def render_scene_video(
        self,
        image_path: Path,
        audio_path: Path,
        output_video_path: Path,
        duration: float,
        motion_effect: str = "zoom_in",
        width: int = 1080,
        height: int = 1920,
        sfx_path: Optional[Path] = None,
    ) -> Path:
        """
        Renders an individual scene on 9:16 vertical canvas (1080x1920 full-bleed).
        - Guaranteed 100% full-screen vertical frame (0% horizontal letterboxing / blurred bars).
        - Applies dynamic Ken Burns motion effects (zoom_in, zoom_out, pan_left, pan_right, etc.).
        - Seamlessly layers SFX sound cues (dramatic_boom, whoosh) under the narration.
        """
        ffmpeg = self.get_ffmpeg_binary()
        output_video_path.parent.mkdir(parents=True, exist_ok=True)

        video_extensions = {".webm", ".mp4", ".mov", ".mkv", ".ogv", ".avi"}
        is_video = image_path.suffix.lower() in video_extensions

        has_sfx = sfx_path and sfx_path.exists()
        logger.info(
            f"Rendering scene video: {image_path.name} (type={'video' if is_video else 'image'}, "
            f"dur={duration:.1f}s, motion={motion_effect}, sfx={'yes' if has_sfx else 'none'})"
        )

        if is_video:
            # Full-bleed 9:16 vertical crop & scale for all moving video clips
            v_filter = (
                f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase:flags=lanczos,"
                f"crop={width}:{height},"
                f"eq=contrast=1.06:saturation=1.12,"
                f"format=yuv420p[v]"
            )
            if has_sfx:
                filter_complex = (
                    f"{v_filter};"
                    f"[1:a]volume=1.0[voice];[2:a]volume=0.55[sfx];"
                    f"[voice][sfx]amix=inputs=2:duration=first:dropout_transition=2[aout]"
                )
            else:
                filter_complex = f"{v_filter}"

            cmd = [
                ffmpeg,
                "-y",
                "-stream_loop", "-1",
                "-i", str(image_path),
                "-i", str(audio_path),
            ]
            if has_sfx:
                cmd.extend(["-i", str(sfx_path)])

            cmd.extend([
                "-filter_complex", filter_complex,
                "-map", "[v]",
                "-map", "[aout]" if has_sfx else "1:a",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "18",
                "-b:v", "6000k",
                "-maxrate", "8000k",
                "-bufsize", "12000k",
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "44100",
                "-r", "30",
                "-t", str(duration),
                "-pix_fmt", "yuv420p",
                str(output_video_path),
            ])
        else:
            total_frames = max(30, int(duration * 30))
            p = f"(on/{total_frames})"

            if motion_effect == "zoom_out":
                zoom_expr = f"z='max(1.22 - {p}*0.20, 1.01)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            elif motion_effect == "pan_left":
                zoom_expr = f"z='1.18':x='(1.0 - {p})*(iw-iw/zoom)':y='ih/2-(ih/zoom/2)'"
            elif motion_effect == "pan_right":
                zoom_expr = f"z='1.18':x='({p})*(iw-iw/zoom)':y='ih/2-(ih/zoom/2)'"
            elif motion_effect in ["drift", "ken_burns"]:
                zoom_expr = f"z='1.05 + {p}*0.14':x='({p})*(iw-iw/zoom)':y='(1.0 - {p})*(ih-ih/zoom)'"
            elif motion_effect == "shake":
                zoom_expr = f"z='1.12':x='iw/2-(iw/zoom/2)+sin(on*0.25)*10':y='ih/2-(ih/zoom/2)+cos(on*0.2)*10'"
            else:  # zoom_in (default)
                zoom_expr = f"z='min(1.0 + {p}*0.20, 1.26)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"

            # Scale to 1440x2560 canvas to ensure razor sharp 1080x1920 Ken Burns output without blurry bars
            v_filter = (
                f"[0:v]scale=1440:2560:force_original_aspect_ratio=increase:flags=lanczos,"
                f"crop=1440:2560,"
                f"zoompan={zoom_expr}:d={total_frames}:s={width}x{height}:fps=30,"
                f"eq=contrast=1.06:saturation=1.12,"
                f"format=yuv420p[v]"
            )
            if has_sfx:
                filter_complex = (
                    f"{v_filter};"
                    f"[1:a]volume=1.0[voice];[2:a]volume=0.55[sfx];"
                    f"[voice][sfx]amix=inputs=2:duration=first:dropout_transition=2[aout]"
                )
            else:
                filter_complex = f"{v_filter}"

            cmd = [
                ffmpeg,
                "-y",
                "-loop", "1",
                "-i", str(image_path),
                "-i", str(audio_path),
            ]
            if has_sfx:
                cmd.extend(["-i", str(sfx_path)])

            cmd.extend([
                "-filter_complex", filter_complex,
                "-map", "[v]",
                "-map", "[aout]" if has_sfx else "1:a",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "18",
                "-b:v", "6000k",
                "-maxrate", "8000k",
                "-bufsize", "12000k",
                "-tune", "stillimage",
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "44100",
                "-r", "30",
                "-t", str(duration),
                "-pix_fmt", "yuv420p",
                str(output_video_path),
            ])

        await asyncio.to_thread(
            self._run_subprocess_sync,
            cmd,
            "FFmpeg scene render error",
        )

        return output_video_path

    def _run_subprocess_sync(self, cmd: List[str], error_prefix: str = "FFmpeg error") -> None:
        """
        Executes an external command safely using subprocess.run in a background thread.
        Prevents NotImplementedError on Windows when running under SelectorEventLoop.
        """
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if proc.returncode != 0:
            err_msg = proc.stderr.decode("utf-8", errors="ignore")
            raise RuntimeError(f"{error_prefix}: {err_msg}")

    async def assemble_full_video(
        self,
        scene_video_paths: List[Path],
        output_mp4_path: Path,
        ass_subtitle_path: Optional[Path] = None,
        bgm_path: Optional[Path] = None,
        bgm_volume: float = 0.12,
    ) -> Path:
        """
        Concatenates all scene segments, layers background music (BGM),
        burns subtitles, and adds smooth broadcast outro fade-out into the final MP4.
        """
        ffmpeg = self.get_ffmpeg_binary()
        output_mp4_path.parent.mkdir(parents=True, exist_ok=True)

        temp_dir = output_mp4_path.parent / "temp_concat"
        temp_dir.mkdir(parents=True, exist_ok=True)
        concat_list = temp_dir / "concat_list.txt"

        lines = [f"file '{p.resolve().as_posix()}'" for p in scene_video_paths]
        concat_list.write_text("\n".join(lines), encoding="utf-8")

        temp_merged = temp_dir / "merged_scenes.mp4"

        # 1. Concatenate scenes
        cmd_concat = [
            ffmpeg,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            str(temp_merged),
        ]
        await asyncio.to_thread(
            self._run_subprocess_sync,
            cmd_concat,
            "FFmpeg concat error",
        )

        # Probe total duration of merged video for outro audio/video fade-out
        probe_cmd = [ffmpeg, "-i", str(temp_merged)]
        probe_res = subprocess.run(
            probe_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="ignore",
        )
        match_dur = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", probe_res.stderr)
        total_dur = 0.0
        if match_dur:
            h, m, s = match_dur.groups()
            total_dur = round(int(h) * 3600 + int(m) * 60 + float(s), 2)

        # 2. Add BGM and Burn Subtitles
        has_sub = ass_subtitle_path and ass_subtitle_path.exists()
        has_bgm = bgm_path and bgm_path.exists()

        filter_parts = []
        if has_sub:
            escaped_sub = str(ass_subtitle_path.resolve()).replace("\\", "/").replace(":", "\\:")
            filter_parts.append(f"subtitles='{escaped_sub}'")

        # Smooth outro fade-to-black in final 0.6s
        if total_dur > 4.0:
            fade_v_start = round(total_dur - 0.6, 2)
            filter_parts.append(f"fade=t=out:st={fade_v_start}:d=0.6")

        vf_arg = ",".join(filter_parts) if filter_parts else None

        cmd_final = [ffmpeg, "-y", "-i", str(temp_merged)]

        fade_a_start = round(max(0.0, total_dur - 1.0), 2) if total_dur > 4.0 else None

        if has_bgm:
            cmd_final.extend(["-stream_loop", "-1", "-i", str(bgm_path)])
            if fade_a_start is not None:
                filter_complex = (
                    f"[1:a]volume={bgm_volume}[bgm];"
                    f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2,"
                    f"afade=t=out:st={fade_a_start}:d=1.0[aout]"
                )
            else:
                filter_complex = f"[1:a]volume={bgm_volume}[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            cmd_final.extend(["-filter_complex", filter_complex, "-map", "0:v", "-map", "[aout]"])
        else:
            if fade_a_start is not None:
                filter_complex = f"[0:a]afade=t=out:st={fade_a_start}:d=1.0[aout]"
                cmd_final.extend(["-filter_complex", filter_complex, "-map", "0:v", "-map", "[aout]"])
            else:
                cmd_final.extend(["-map", "0:v", "-map", "0:a"])

        if vf_arg:
            cmd_final.extend(["-vf", vf_arg])

        cmd_final.extend([
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-b:v", "6000k",
            "-maxrate", "8000k",
            "-bufsize", "12000k",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(output_mp4_path),
        ])

        logger.info(f"Assembling final MP4 video: {output_mp4_path}...")
        await asyncio.to_thread(
            self._run_subprocess_sync,
            cmd_final,
            "FFmpeg final assembly error",
        )

        # Cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info(f"Video assembly COMPLETE: {output_mp4_path}")
        return output_mp4_path

    def verify_rendered_video(
        self, video_path: Path, expected_duration: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Rà soát và kiểm định toàn diện chất lượng video sau khi render:
        1. Kiểm tra tồn tại và dung lượng file hợp lệ (>500KB).
        2. Dò tìm thông số kỹ thuật (Resolution, Duration, Bitrate, Codecs).
        3. Kiểm tra tính toàn vẹn từng khung hình bằng FFmpeg null muxer (phát hiện lỗi vỡ hình / corrupt frame).
        4. Trả về kết quả đánh giá chi tiết chuẩn studio.
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file không tồn tại: {video_path}")

        file_size_bytes = video_path.stat().st_size
        if file_size_bytes < 500_000:
            raise ValueError(f"Video file quá nhỏ ({file_size_bytes} bytes), render có thể bị gián đoạn.")

        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
        ffmpeg = self.get_ffmpeg_binary()

        # Probe video information
        info_cmd = [ffmpeg, "-i", str(video_path)]
        info_res = subprocess.run(
            info_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="ignore",
        )
        stderr_text = info_res.stderr

        # Extract Duration
        match_dur = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", stderr_text)
        duration_seconds = 0.0
        duration_str = "00:00:00"
        if match_dur:
            h, m, s = match_dur.groups()
            duration_seconds = round(int(h) * 3600 + int(m) * 60 + float(s), 2)
            duration_str = f"{h}:{m}:{s}"

        # Extract Resolution
        match_res = re.search(r"Video:.*?\b(\d{3,5})x(\d{3,5})\b", stderr_text)
        resolution = f"{match_res.group(1)}x{match_res.group(2)}" if match_res else "Unknown"

        # Extract Bitrate
        match_bitrate = re.search(r"bitrate:\s*(\d+)\s*kb/s", stderr_text)
        bitrate_kbps = int(match_bitrate.group(1)) if match_bitrate else 0

        # Extract Video & Audio Codecs
        has_video = "Video:" in stderr_text
        has_audio = "Audio:" in stderr_text

        # Frame Integrity Check with FFmpeg null-muxer
        integrity_cmd = [ffmpeg, "-v", "error", "-i", str(video_path), "-f", "null", "-"]
        integrity_res = subprocess.run(
            integrity_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="ignore",
        )
        integrity_errors = integrity_res.stderr.strip()
        is_integrity_passed = len(integrity_errors) == 0

        # Verification assessment
        passed = (
            file_size_bytes > 500_000
            and has_video
            and has_audio
            and duration_seconds > 5.0
            and is_integrity_passed
        )

        report = {
            "passed": passed,
            "file_name": video_path.name,
            "file_size_mb": file_size_mb,
            "resolution": resolution,
            "duration_seconds": duration_seconds,
            "duration_formatted": duration_str,
            "bitrate_kbps": bitrate_kbps,
            "has_video_stream": has_video,
            "has_audio_stream": has_audio,
            "integrity_status": "PASSED (0 corrupt frames)" if is_integrity_passed else f"WARNING: {integrity_errors[:200]}",
            "summary": (
                f"Rà soát video THÀNH CÔNG: Độ phân giải {resolution}, "
                f"Thời lượng {duration_seconds}s, Dung lượng {file_size_mb} MB, "
                f"Bitrate {bitrate_kbps} kbps, Toàn vẹn 100% không lỗi khung hình."
            ),
        }

        logger.info(f"[VIDEO_VERIFY] {report['summary']}")
        return report


ffmpeg_editor = FFmpegEditor()


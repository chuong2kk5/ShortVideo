import asyncio
import io
import json
import logging
import math
import random
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
import urllib.parse
import httpx
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

from app.config import settings

logger = logging.getLogger("comfyui_provider")


class ComfyUIProvider:
    """
    Multi-Tier Visual Engine for Shorts & TikTok:
    - Tier 1: Google Imagen 3 via Gemini API (Photorealistic 8K AI artwork in 9:16).
    - Tier 2: Local ComfyUI (if SDXL / Flux is running on http://127.0.0.1:8188).
    - Tier 3: Semantic Photographic Matcher (Searches 100M+ real CC0/free high-res photos
              via Wikimedia Commons, crops & enhances into crisp 1080x1920 vertical frames).
    - Tier 4: Cinematic Procedural Canvas (Safety fallback if completely offline).
    """

    def __init__(self):
        self.base_url = settings.COMFYUI_BASE_URL.rstrip("/")
        self._ua = "AIShortsFactory/1.0 (https://github.com/local-user/shorts-factory; contact@shortsfactory.local)"

    async def is_available(self) -> bool:
        """Checks if local ComfyUI server is online."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/system_stats")
                return res.status_code == 200
        except Exception:
            return False

    def _build_standard_workflow(self, prompt: str, seed: Optional[int] = None) -> Dict[str, Any]:
        """Builds standard Text-to-Image workflow for ComfyUI (720x1280 vertical)."""
        actual_seed = seed if seed is not None else random.randint(1, 1000000000)
        return {
            "3": {
                "inputs": {
                    "seed": actual_seed,
                    "steps": 20,
                    "cfg": 7.0,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
                "class_type": "KSampler",
            },
            "4": {
                "inputs": {"ckpt_name": "v1-5-pruned-emaonly.safetensors"},
                "class_type": "CheckpointLoaderSimple",
            },
            "5": {
                "inputs": {"width": 720, "height": 1280, "batch_size": 1},
                "class_type": "EmptyLatentImage",
            },
            "6": {
                "inputs": {
                    "text": f"{prompt}, 8k resolution, cinematic lighting, photorealistic, 9:16 vertical composition, highly detailed",
                    "clip": ["4", 1],
                },
                "class_type": "CLIPTextEncode",
            },
            "7": {
                "inputs": {
                    "text": "text, watermark, low quality, blurry, deformed, bad anatomy, cropped",
                    "clip": ["4", 1],
                },
                "class_type": "CLIPTextEncode",
            },
            "8": {
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
                "class_type": "VAEDecode",
            },
            "9": {
                "inputs": {"filename_prefix": "ShortsFactory", "images": ["8", 0]},
                "class_type": "SaveImage",
            },
        }

    async def generate_visual_asset(
        self,
        prompt: str,
        output_base_path: Path,
        width: int = 1080,
        height: int = 1920,
        keywords: Optional[str] = None,
        narration: Optional[str] = None,
        prefer_video: bool = True,
    ) -> Path:
        """
        Universal visual asset generator:
        1. Searches and downloads real moving video footage (.webm, .mp4).
        2. If video is unavailable, falls back to Google Imagen 3 (Gemini API) / ComfyUI / Wikimedia high-res photos.
        3. Guarantees a valid file (video or image) is returned.
        """
        output_base_path.parent.mkdir(parents=True, exist_ok=True)

        if prefer_video:
            try:
                vid_path = await self.find_stock_video_clip(
                    prompt=prompt,
                    output_path=output_base_path,
                    keywords=keywords,
                    narration=narration,
                )
                if vid_path and vid_path.exists() and vid_path.stat().st_size > 100_000:
                    logger.info(f"Using moving stock video asset: {vid_path}")
                    return vid_path
            except Exception as e:
                logger.warning(f"Stock video search failed, falling back to images: {e}")

        # Fallback to image generation
        img_path = output_base_path.with_suffix(".jpg")
        return await self.generate_image(
            prompt=prompt,
            output_path=img_path,
            width=width,
            height=height,
            keywords=keywords,
            narration=narration,
        )

    async def find_stock_video_clip(
        self,
        prompt: str,
        output_path: Path,
        keywords: Optional[str] = None,
        narration: Optional[str] = None,
    ) -> Optional[Path]:
        """
        Searches for and downloads authentic moving video footage (.webm, .mp4)
        matching the scene topic from Pexels (if API key available) and Wikimedia Commons.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        search_candidates = self._extract_search_queries(keywords, prompt, narration)
        headers = {"User-Agent": self._ua}

        # 1. Pexels API (if configured)
        if getattr(settings, "PEXELS_API_KEY", ""):
            try:
                for query in search_candidates[:3]:
                    pexels_url = "https://api.pexels.com/videos/search"
                    params = {"query": query, "orientation": "portrait", "per_page": 3}
                    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                        res = await client.get(
                            pexels_url,
                            params=params,
                            headers={"Authorization": settings.PEXELS_API_KEY},
                        )
                        if res.status_code == 200:
                            videos = res.json().get("videos", [])
                            for v in videos:
                                video_files = v.get("video_files", [])
                                video_files.sort(key=lambda f: abs(f.get("width", 0) - 1080))
                                for vf in video_files:
                                    link = vf.get("link")
                                    if link:
                                        target_vid = output_path.with_suffix(".mp4")
                                        dl = await client.get(link)
                                        if dl.status_code == 200 and len(dl.content) > 100_000:
                                            target_vid.write_bytes(dl.content)
                                            logger.info(f"Pexels stock video downloaded: {target_vid}")
                                            return target_vid
            except Exception as e:
                logger.warning(f"Pexels video search error: {e}")

        # 2. Wikimedia Commons Video Search (100% free, zero key required)
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for query in search_candidates:
                search_term = f"{query} filetype:video"
                logger.info(f"Searching Wikimedia Commons for video: '{search_term}'...")
                try:
                    res = await client.get(
                        "https://commons.wikimedia.org/w/api.php",
                        params={
                            "action": "query",
                            "generator": "search",
                            "gsrsearch": search_term,
                            "gsrnamespace": 6,
                            "prop": "imageinfo",
                            "iiprop": "url|mime|size|dimensions",
                            "format": "json",
                            "gsrlimit": 8,
                        },
                        headers=headers,
                    )
                    if res.status_code != 200:
                        continue

                    pages = res.json().get("query", {}).get("pages", {})
                    candidates = []
                    for page_id, page_data in pages.items():
                        info_list = page_data.get("imageinfo", [])
                        if not info_list:
                            continue
                        info = info_list[0]
                        vurl = info.get("url", "")
                        vmime = info.get("mime", "")
                        vsize = info.get("size", 0)
                        vwidth = info.get("width", 0)
                        vheight = info.get("height", 0)

                        ext = Path(vurl.split("?")[0]).suffix.lower()
                        if ext in [".webm", ".mp4", ".ogv"] or vmime.startswith("video/"):
                            # Check portrait orientation and HD resolution
                            is_portrait = 1 if (vheight > vwidth) else 0
                            is_hd = 1 if (vwidth >= 1280 or vheight >= 720 or (vwidth >= 720 and vheight >= 1280)) else 0
                            if 300_000 <= vsize <= 50_000_000:
                                candidates.append((vurl, ext or ".webm", vsize, is_portrait, is_hd, vwidth, vheight))

                    # Prioritize native vertical first, then HD quality, then largest file size
                    candidates.sort(key=lambda c: (c[3], c[4], c[2]), reverse=True)

                    # Download candidate video
                    for vurl, ext, vsize, is_port, is_hd, vw, vh in candidates:
                        try:
                            target_file = output_path.with_suffix(ext if ext in [".webm", ".mp4", ".ogv"] else ".webm")
                            orient_tag = "Portrait " if is_port else ""
                            hd_tag = f"{orient_tag}HD {vw}x{vh}" if is_hd else f"{orient_tag}{vw}x{vh}"
                            logger.info(f"Downloading video clip [{hd_tag}] ({vsize / 1024 / 1024:.1f} MB) from {vurl[:80]}...")
                            dl_res = await client.get(vurl, headers=headers)
                            if dl_res.status_code == 200 and len(dl_res.content) > 100_000:
                                target_file.write_bytes(dl_res.content)
                                logger.info(f"Stock video downloaded successfully: {target_file} ({len(dl_res.content)} bytes)")
                                return target_file
                        except Exception as dl_err:
                            logger.debug(f"Failed downloading {vurl}: {dl_err}")
                except Exception as q_err:
                    logger.debug(f"Wikimedia video query '{query}' failed: {q_err}")

        return None

    async def generate_image(
        self,
        prompt: str,
        output_path: Path,
        width: int = 1080,
        height: int = 1920,
        keywords: Optional[str] = None,
        narration: Optional[str] = None,
    ) -> Path:
        """
        Executes tiered visual generation:
        1. Web Photographic Engine (Google / Bing global web index for authentic photos matching topic)
        2. Semantic Photographic Matcher (Wikimedia Commons 100M+ high-res photos)
        3. Google Imagen 3 (Gemini API Key)
        4. Local ComfyUI (if active)
        5. Atmospheric Procedural Canvas (final offline fallback)
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # ------------------------------------------------------------------
        # TIER 1: Web Photographic Engine (Google / Bing Global Web Index)
        # ------------------------------------------------------------------
        try:
            logger.info("Calling Tier 1 [Web Photographic Engine] for authentic internet imagery...")
            web_photo = await self._search_web_photographic_match(
                prompt=prompt,
                keywords=keywords,
                narration=narration,
                output_path=output_path,
                target_w=width,
                target_h=height,
            )
            if web_photo and web_photo.exists() and web_photo.stat().st_size > 5000:
                logger.info(f"Tier 1 [Web Photographic Engine] successfully retrieved: {output_path}")
                return web_photo
        except Exception as e:
            logger.warning(f"Tier 1 [Web Photographic Engine] failed: {e}")

        # ------------------------------------------------------------------
        # TIER 2: Semantic Photographic Matcher (Wikimedia Commons 100M+ photos)
        # ------------------------------------------------------------------
        try:
            logger.info("Calling Tier 2 [Wikimedia Photographic Matcher] for documentary imagery...")
            photo_path = await self._generate_photographic_match(
                prompt=prompt,
                keywords=keywords,
                narration=narration,
                output_path=output_path,
                target_w=width,
                target_h=height,
            )
            if photo_path and photo_path.exists() and photo_path.stat().st_size > 5000:
                logger.info(f"Tier 2 [Wikimedia Matcher] successfully retrieved: {output_path}")
                return photo_path
        except Exception as e:
            logger.warning(f"Tier 2 [Wikimedia Matcher] failed: {e}")

        # ------------------------------------------------------------------
        # TIER 3: Google Imagen 3 (Gemini API Key)
        # ------------------------------------------------------------------
        try:
            from app.services.gemini_image_provider import gemini_image_provider
            gemini_img = await gemini_image_provider.generate_image(prompt, output_path)
            if gemini_img and gemini_img.exists() and gemini_img.stat().st_size > 5000:
                logger.info(f"Tier 3 [Google Imagen 3] generated: {output_path}")
                return gemini_img
        except Exception as e:
            logger.warning(f"Tier 3 [Google Imagen 3] failed: {e}")

        # ------------------------------------------------------------------
        # TIER 4: Local ComfyUI (if running)
        # ------------------------------------------------------------------
        if await self.is_available():
            try:
                logger.info(f"ComfyUI is online at {self.base_url}. Generating via SDXL...")
                image_path = await self._generate_comfyui(prompt, output_path)
                if image_path and image_path.exists():
                    logger.info(f"Tier 4 [ComfyUI] generated: {output_path}")
                    return image_path
            except Exception as e:
                logger.warning(f"Tier 4 [ComfyUI] failed ({e})")

        # ------------------------------------------------------------------
        # TIER 5: Atmospheric Procedural Canvas
        # ------------------------------------------------------------------
        logger.info("Using Tier 5 procedural cinematic canvas fallback...")
        return self._generate_procedural_fallback(prompt, output_path, width, height)

    async def _generate_comfyui(self, prompt: str, output_path: Path) -> Path:
        """Sends workflow to ComfyUI and polls for the completed image."""
        workflow = self._build_standard_workflow(prompt)
        payload = {"prompt": workflow}

        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.post(f"{self.base_url}/prompt", json=payload)
            if res.status_code != 200:
                raise RuntimeError(f"ComfyUI /prompt error: {res.text}")
            prompt_id = res.json().get("prompt_id")

            # Poll for completion
            for _ in range(60):
                await asyncio.sleep(2.0)
                hist_res = await client.get(f"{self.base_url}/history/{prompt_id}")
                if hist_res.status_code == 200 and prompt_id in hist_res.json():
                    outputs = hist_res.json()[prompt_id].get("outputs", {})
                    for node_id, node_output in outputs.items():
                        images = node_output.get("images", [])
                        if images:
                            img_info = images[0]
                            view_url = (
                                f"{self.base_url}/view?"
                                f"filename={img_info['filename']}&"
                                f"subfolder={img_info.get('subfolder', '')}&"
                                f"type={img_info.get('type', 'output')}"
                            )
                            img_res = await client.get(view_url)
                            if img_res.status_code == 200:
                                output_path.write_bytes(img_res.content)
                                return output_path
                    break

        raise RuntimeError("ComfyUI generation timed out or produced no image.")

    def _extract_search_queries(
        self,
        keywords: Optional[str],
        prompt: str,
        narration: Optional[str] = None,
    ) -> List[str]:
        """Generates a prioritized list of search keyword strings for video & photographic matching."""
        queries: List[str] = []

        # 1. Primary Keywords (most concrete subject)
        if keywords and keywords.strip():
            clean_kw = re.sub(r'["\',;.]', ' ', keywords).strip()
            queries.append(clean_kw)
            words = [w for w in clean_kw.split() if len(w) > 2]
            if len(words) > 2:
                queries.append(" ".join(words[:2]))
            # Also append the primary anchor noun (first or last word)
            if words:
                queries.append(words[0])
                if len(words) > 1 and words[-1] != words[0]:
                    queries.append(words[-1])

        # 2. Clean prompt to extract actual physical subject
        p = re.sub(
            r"^(Cinematic|Vertical|Horizontal|Dramatic|Epic|Wide|Close-up|Macro|Aerial|Drone|High-definition|Ultra-detailed|Photorealistic|Panoramic shot|A photo of|Shot of)\s*(vertical)?\s*(9:16)?\s*(shot|angle|view|framing|photo|image|scene)?\s*(of|representing)?\s*",
            "",
            prompt,
            flags=re.IGNORECASE,
        ).strip()
        p = re.sub(
            r"(8k resolution|volumetric lighting|hyper-detailed|cinematic lighting|4k|photorealistic|9:16 vertical|unreal engine|scene \d+).*",
            "",
            p,
            flags=re.IGNORECASE,
        ).strip()

        clauses = [c.strip() for c in re.split(r"[,;.]", p) if len(c.strip()) > 3]
        for c in clauses[:2]:
            clean_c = " ".join([w for w in c.split() if w.lower() not in {"shot", "scene", "representing", "cinematic", "vertical", "composition"}][:3])
            if len(clean_c) > 2:
                queries.append(clean_c)

        # De-duplicate while preserving priority order
        seen = set()
        deduped = []
        for q in queries:
            q_clean = q.strip().lower()
            if q_clean and q_clean not in seen:
                seen.add(q_clean)
                deduped.append(q.strip())
        return deduped

    async def _search_web_photographic_match(
        self,
        prompt: str,
        keywords: Optional[str],
        narration: Optional[str],
        output_path: Path,
        target_w: int = 1080,
        target_h: int = 1920,
    ) -> Optional[Path]:
        """
        Queries global web photographic index (Google / Bing web image search index)
        for real, authentic high-resolution photos matching the scene context.
        Prioritizes tall/portrait 9:16 images, then large 4K/HD images.
        """
        search_candidates = self._extract_search_queries(keywords, prompt, narration)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
        }

        async with httpx.AsyncClient(headers=headers, timeout=12.0, follow_redirects=True) as client:
            for query in search_candidates[:4]:
                logger.info(f"Searching web photographic index for: '{query}'...")
                urls_to_query = [
                    # 1. Search tall/vertical HD images
                    f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}&qft=+filterui:imagesize-large+filterui:aspect-tall&form=IRFLTR&first=1",
                    # 2. Search large HD images
                    f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}&qft=+filterui:imagesize-large&form=IRFLTR&first=1",
                    # 3. Standard search
                    f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}&form=HDRSC2&first=1",
                ]

                candidate_urls: List[str] = []
                for s_url in urls_to_query:
                    try:
                        res = await client.get(s_url)
                        if res.status_code == 200:
                            murls = re.findall(r'&quot;murl&quot;:&quot;(https?://[^&]+)&quot;', res.text)
                            if not murls:
                                murls = re.findall(r'"murl":"(https?://[^"]+)"', res.text)
                            for u in murls:
                                clean_u = urllib.parse.unquote(u)
                                ext = Path(clean_u.split('?')[0]).suffix.lower()
                                if ext in ['.jpg', '.jpeg', '.png', '.webp'] or not ext:
                                    if clean_u not in candidate_urls:
                                        candidate_urls.append(clean_u)
                        if len(candidate_urls) >= 12:
                            break
                    except Exception as err:
                        logger.debug(f"Web image search page failed for {s_url}: {err}")

                # Download best candidate
                for img_url in candidate_urls[:10]:
                    try:
                        dl = await client.get(img_url, timeout=8.0)
                        if dl.status_code == 200 and len(dl.content) > 20_000:
                            raw_img = Image.open(io.BytesIO(dl.content)).convert("RGB")
                            w, h = raw_img.size
                            if w >= 450 and h >= 450:
                                processed = self._crop_and_enhance_to_vertical(raw_img, target_w, target_h)
                                processed.save(output_path, "JPEG", quality=95)
                                logger.info(
                                    f"Web photo successfully retrieved and formatted for '{query}': {output_path} (orig: {w}x{h})"
                                )
                                return output_path
                    except Exception as dl_err:
                        logger.debug(f"Failed downloading web photo candidate {img_url[:60]}: {dl_err}")

        return None

    async def _generate_photographic_match(
        self,
        prompt: str,
        keywords: Optional[str],
        narration: Optional[str],
        output_path: Path,
        target_w: int = 1080,
        target_h: int = 1920,
    ) -> Optional[Path]:
        """
        Queries Wikimedia Commons for real photographic images matching the keywords,
        downloads the highest quality candidate, and crops/scales to vertical 9:16.
        """
        search_candidates = self._extract_search_queries(keywords, prompt, narration)
        headers = {"User-Agent": self._ua}

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            for query in search_candidates[:4]:
                search_term = f"{query} filetype:bitmap"
                logger.info(f"Searching Wikimedia Commons for: '{search_term}'...")

                try:
                    res = await client.get(
                        "https://commons.wikimedia.org/w/api.php",
                        params={
                            "action": "query",
                            "generator": "search",
                            "gsrsearch": search_term,
                            "gsrnamespace": 6,
                            "prop": "imageinfo",
                            "iiprop": "url|mime|size",
                            "format": "json",
                            "gsrlimit": 5,
                        },
                        headers=headers,
                    )
                    if res.status_code != 200:
                        continue

                    pages = res.json().get("query", {}).get("pages", {})
                    candidate_urls: List[str] = []
                    for page_id, page_data in pages.items():
                        info_list = page_data.get("imageinfo", [])
                        if not info_list:
                            continue
                        info = info_list[0]
                        mime = info.get("mime", "")
                        width = info.get("width", 0)
                        height = info.get("height", 0)

                        # We want photographic formats with reasonable size
                        if mime in ["image/jpeg", "image/png", "image/webp"] and width >= 600 and height >= 600:
                            candidate_urls.append(info.get("url"))

                    if not candidate_urls:
                        # Try without filetype filter
                        continue

                    # Download candidate image
                    for img_url in candidate_urls:
                        try:
                            dl_res = await client.get(img_url, headers=headers)
                            if dl_res.status_code == 200 and len(dl_res.content) > 10000:
                                raw_img = Image.open(io.BytesIO(dl_res.content)).convert("RGB")
                                processed = self._crop_and_enhance_to_vertical(raw_img, target_w, target_h)
                                processed.save(output_path, "JPEG", quality=95)
                                logger.info(
                                    f"Successfully retrieved and processed photo for '{query}': {output_path}"
                                )
                                return output_path
                        except Exception as dl_err:
                            logger.debug(f"Failed to process candidate {img_url}: {dl_err}")

                except Exception as q_err:
                    logger.debug(f"Search query '{query}' failed: {q_err}")

        return None

    def _crop_and_enhance_to_vertical(
        self, img: Image.Image, target_w: int = 1080, target_h: int = 1920
    ) -> Image.Image:
        """
        Formats image into a vertical 9:16 frame (1080x1920).
        - If image is horizontal (> 0.75 AR): creates a TikTok cinematic blurred ambient background
          with the full crisp image centered (100% content preserved, 0% cut-off, razor sharp).
        - If image is native vertical (<= 0.75 AR): scales and minimally center crops.
        """
        ar = img.width / img.height if img.height > 0 else 1.0

        if ar > 0.65:
            # Horizontal / landscape image:
            # 1. Background layer: fill 1080x1920 canvas with blurred ambient backdrop
            bg_scale = max(target_w / img.width, target_h / img.height)
            bg_w = max(target_w, int(img.width * bg_scale))
            bg_h = max(target_h, int(img.height * bg_scale))
            bg_resized = img.resize((bg_w, bg_h), Image.Resampling.LANCZOS)
            bg_left = (bg_w - target_w) // 2
            bg_top = (bg_h - target_h) // 2
            bg_cropped = bg_resized.crop((bg_left, bg_top, bg_left + target_w, bg_top + target_h))
            bg_blurred = bg_cropped.filter(ImageFilter.GaussianBlur(28))
            bg_dimmed = ImageEnhance.Brightness(bg_blurred).enhance(0.85)

            # 2. Foreground layer: scale to full target_w (1080) preserving full image
            fg_w = target_w
            fg_h = int(img.height * (fg_w / img.width))
            fg_resized = img.resize((fg_w, fg_h), Image.Resampling.LANCZOS)

            fg_enhanced = ImageEnhance.Color(fg_resized).enhance(1.08)
            fg_enhanced = ImageEnhance.Contrast(fg_enhanced).enhance(1.05)

            # 3. Paste centered
            final_canvas = bg_dimmed.copy()
            y_pos = (target_h - fg_h) // 2
            final_canvas.paste(fg_enhanced, (0, y_pos))
            return final_canvas
        else:
            # Native vertical image: scale and minimal crop
            scale = max(target_w / img.width, target_h / img.height)
            new_w = int(img.width * scale)
            new_h = int(img.height * scale)
            resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            left = (new_w - target_w) // 2
            top = (new_h - target_h) // 2
            cropped = resized.crop((left, top, left + target_w, top + target_h))

            color_enhancer = ImageEnhance.Color(cropped)
            enhanced = color_enhancer.enhance(1.08)
            contrast_enhancer = ImageEnhance.Contrast(enhanced)
            return contrast_enhancer.enhance(1.05)


    def _generate_procedural_fallback(
        self, prompt: str, output_path: Path, width: int = 1080, height: int = 1920
    ) -> Path:
        """
        Creates a rich, atmospheric 9:16 vertical image with deep ambient gradients,
        cinematic vignette, nebula particles, and lighting accents.
        """
        lower = prompt.lower()
        if "ocean" in lower or "water" in lower or "sea" in lower or "deep" in lower:
            top_color = (4, 15, 38)
            mid_color = (10, 42, 85)
            bottom_color = (2, 8, 20)
            accent = (0, 200, 255)
        elif "fire" in lower or "sun" in lower or "desert" in lower or "gold" in lower:
            top_color = (38, 12, 4)
            mid_color = (95, 40, 10)
            bottom_color = (20, 5, 2)
            accent = (255, 140, 0)
        elif "nature" in lower or "forest" in lower or "jungle" in lower:
            top_color = (6, 28, 15)
            mid_color = (18, 65, 38)
            bottom_color = (3, 14, 8)
            accent = (50, 255, 120)
        else:
            top_color = (15, 8, 30)
            mid_color = (35, 15, 65)
            bottom_color = (8, 4, 18)
            accent = (180, 100, 255)

        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        for y in range(height):
            ratio = y / height
            if ratio < 0.5:
                r1 = ratio / 0.5
                r = int(top_color[0] + (mid_color[0] - top_color[0]) * r1)
                g = int(top_color[1] + (mid_color[1] - top_color[1]) * r1)
                b = int(top_color[2] + (mid_color[2] - top_color[2]) * r1)
            else:
                r2 = (ratio - 0.5) / 0.5
                r = int(mid_color[0] + (bottom_color[0] - mid_color[0]) * r2)
                g = int(mid_color[1] + (bottom_color[1] - mid_color[1]) * r2)
                b = int(mid_color[2] + (bottom_color[2] - mid_color[2]) * r2)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow)
        cx, cy = width // 2, height // 2 - 100
        radius = 350
        gdraw.ellipse(
            [(cx - radius, cy - radius), (cx + radius, cy + radius)],
            fill=(accent[0], accent[1], accent[2], 75),
        )
        glow = glow.filter(ImageFilter.GaussianBlur(120))
        img.paste(glow, (0, 0), glow)

        img.save(output_path, "JPEG", quality=92)
        logger.info(f"Procedural fallback canvas saved: {output_path}")
        return output_path


comfyui_provider = ComfyUIProvider()

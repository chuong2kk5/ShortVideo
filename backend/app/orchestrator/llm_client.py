import json
import logging
import re
from typing import Dict, Any, Optional
import httpx
from dotenv import dotenv_values
from app.config import settings, BASE_DIR

logger = logging.getLogger("llm_client")


class LLMClient:
    """
    Unified Multi-Provider LLM Client supporting:
    - Ollama (Auto-detects installed models, supports keep_alive: 0 for instant VRAM offloading)
    - Google Gemini REST API (Zero-VRAM, fast)
    - OpenAI / OpenRouter / Custom OpenAI-compatible endpoint
    - Auto-reloads keys from backend/.env dynamically
    """

    def _get_live_env(self) -> Dict[str, str]:
        """Reads .env fresh from disk to capture newly pasted API keys without restarting."""
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            return {k: v for k, v in dotenv_values(str(env_file)).items() if v}
        return {}

    async def check_availability(self) -> Dict[str, Any]:
        """Test reachability of the configured provider."""
        live_env = self._get_live_env()
        provider = live_env.get("LLM_PROVIDER", settings.LLM_PROVIDER).lower()

        status = {
            "configured_provider": provider,
            "available": False,
            "model": "",
            "message": "",
        }

        if provider == "ollama":
            base_url = live_env.get("OLLAMA_BASE_URL", settings.OLLAMA_BASE_URL).rstrip("/")
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    res = await client.get(f"{base_url}/api/tags")
                    if res.status_code == 200:
                        models = res.json().get("models", [])
                        if not models:
                            status["available"] = False
                            status["message"] = "Ollama đang chạy nhưng chưa tải model nào. Mở CMD gõ: 'ollama run qwen2.5:1.5b'"
                        else:
                            status["available"] = True
                            status["model"] = models[0].get("name", "")
                            status["message"] = f"Ollama online với {len(models)} model ({status['model']})"
                    else:
                        status["message"] = f"Ollama trả về mã HTTP {res.status_code}"
            except Exception as e:
                status["message"] = f"Không thể kết nối Ollama tại {base_url}: {e}"

        elif provider == "gemini":
            key = live_env.get("GEMINI_API_KEY", settings.GEMINI_API_KEY)
            status["model"] = live_env.get("GEMINI_MODEL", settings.GEMINI_MODEL)
            if not key:
                status["message"] = "GEMINI_API_KEY chưa được điền trong backend/.env"
            else:
                status["available"] = True
                status["message"] = "Google Gemini API đã được cấu hình."

        elif provider == "openai":
            key = live_env.get("OPENAI_API_KEY", settings.OPENAI_API_KEY)
            status["model"] = live_env.get("OPENAI_MODEL", settings.OPENAI_MODEL)
            if not key:
                status["message"] = "OPENAI_API_KEY chưa được điền trong backend/.env"
            else:
                status["available"] = True
                status["message"] = "OpenAI API đã được cấu hình."

        return status

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
        tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

        live_env = self._get_live_env()
        provider = live_env.get("LLM_PROVIDER", settings.LLM_PROVIDER).lower()
        gemini_key = live_env.get("GEMINI_API_KEY", settings.GEMINI_API_KEY)
        openai_key = live_env.get("OPENAI_API_KEY", settings.OPENAI_API_KEY)

        gemini_error_msg = ""
        ollama_error_msg = ""

        # =====================================================================
        # PRIORITY 1: Google Gemini (if key exists or provider requested)
        # =====================================================================
        if gemini_key:
            logger.info("Priority 1: Attempting script generation with Google Gemini Flash...")
            try:
                return await self._generate_gemini(system_prompt, user_prompt, temp, tokens, gemini_key)
            except Exception as ge:
                gemini_error_msg = str(ge)
                logger.warning(
                    f"Gemini generation failed: {gemini_error_msg}. "
                    "Automatically falling back to local Ollama..."
                )

        # =====================================================================
        # PRIORITY 2: Local Ollama (Fallback from Gemini or Primary if no key)
        # =====================================================================
        logger.info("Priority 2: Attempting script generation with local Ollama...")
        try:
            return await self._generate_ollama(system_prompt, user_prompt, temp, tokens)
        except Exception as oe:
            ollama_error_msg = str(oe)
            logger.warning(f"Ollama execution failed: {ollama_error_msg}. Checking cloud alternatives...")

        # =====================================================================
        # PRIORITY 3: OpenAI (if configured)
        # =====================================================================
        if openai_key:
            logger.info("Priority 3: Attempting script generation with OpenAI...")
            try:
                return await self._generate_openai(system_prompt, user_prompt, temp, tokens, openai_key)
            except Exception as ope:
                logger.warning(f"OpenAI fallback failed: {ope}")

        # =====================================================================
        # PRIORITY 4: Resilient Algorithmic Script ("Không làm không không nữa")
        # Guarantees the pipeline NEVER crashes or returns empty data even offline
        # =====================================================================
        logger.warning(
            "All AI LLMs failed (Gemini: %s, Ollama: %s). Activating Resilient Algorithmic Script Engine...",
            gemini_error_msg or "No API Key",
            ollama_error_msg,
        )
        return self._generate_resilient_fallback_script(user_prompt)

    def _generate_resilient_fallback_script(self, user_prompt: str) -> str:
        """
        Builds a tailored, high-retention 9-scene viral script matching VideoScriptSchema
        when all AI engines are unreachable. Never returns empty.
        """
        # Extract topic
        match_topic = re.search(r'Chủ đề video là:\s*"([^"]+)"', user_prompt)
        topic = match_topic.group(1).strip() if match_topic else "Khám phá thế giới"

        # Determine language
        is_en = "English" in user_prompt or "en" in user_prompt.lower()

        # Clean topic keywords for search
        clean_topic = re.sub(r'[*_`#~\[\]\(\)\{\}\<\>]', '', topic).strip()

        if is_en:
            title = f"Shocking Secrets of {clean_topic}"
            desc = f"Discover astonishing and unexpected facts about {clean_topic}."
            hook = f"Did you know that everything you thought you knew about {clean_topic} is completely wrong?"
            cta = f"What do you think about {clean_topic}? Drop a comment below and subscribe!"
            scenes = [
                {"narration": f"Deep inside the mystery of {clean_topic}, incredible secrets remain hidden.", "visual_keywords": "nature jungle aerial", "motion_effect": "zoom_in", "sound_effect_cue": "whoosh"},
                {"narration": "Scientists have recently discovered mind-blowing details that shock everyone.", "visual_keywords": "waterfall river cascade", "motion_effect": "pan_left", "sound_effect_cue": "dramatic_boom"},
                {"narration": "From the highest peaks to the deepest oceans, the power is undeniable.", "visual_keywords": "mountain peak clouds", "motion_effect": "zoom_out", "sound_effect_cue": "suspense_riser"},
                {"narration": "Apex predators roam free, constantly asserting dominance in the wild.", "visual_keywords": "eagle soaring sky", "motion_effect": "pan_right", "sound_effect_cue": "heartbeat"},
                {"narration": "Every single movement carries intense energy and survival instinct.", "visual_keywords": "lion hunting wild", "motion_effect": "ken_burns", "sound_effect_cue": "camera_flash"},
                {"narration": "Unstoppable forces shape the landscapes over thousands of years.", "visual_keywords": "volcano lava smoke", "motion_effect": "zoom_in", "sound_effect_cue": "dramatic_boom"},
                {"narration": "Glacial ice and burning earth contrast in a dance of nature.", "visual_keywords": "glacier ice ocean", "motion_effect": "pan_left", "sound_effect_cue": "whoosh"},
                {"narration": "Creatures adapt with incredible stealth and unmatched beauty.", "visual_keywords": "leopard stalking tree", "motion_effect": "zoom_out", "sound_effect_cue": "suspense_riser"},
                {"narration": "This timeless wonder reminds us how magnificent our world truly is.", "visual_keywords": "sunset canyon horizon", "motion_effect": "ken_burns", "sound_effect_cue": "heartbeat"},
            ]
        else:
            title = f"Bí Mật Khốc Liệt Về {clean_topic}"
            desc = f"Khám phá những sự thật nghẹt thở và kỳ vĩ nhất về {clean_topic}."
            hook = f"Bạn có bao giờ tự hỏi điều gì thật sự diễn ra sâu thẳm trong {clean_topic}?"
            cta = f"Bạn ấn tượng nhất với chi tiết nào? Để lại bình luận và theo dõi kênh nhé!"
            scenes = [
                {"narration": f"Sâu thẳm trong thế giới của {clean_topic}, những bí ẩn kinh ngạc đang chờ đón.", "visual_keywords": "nature forest aerial", "motion_effect": "zoom_in", "sound_effect_cue": "whoosh"},
                {"narration": "Mỗi khoảnh khắc trôi qua đều là một cuộc chiến sinh tồn đầy kịch tính.", "visual_keywords": "waterfall forest stream", "motion_effect": "pan_left", "sound_effect_cue": "dramatic_boom"},
                {"narration": "Từ trên tầng cao, những kẻ săn mồi sải cánh lượn quanh đầy uy lực.", "visual_keywords": "eagle soaring mountain", "motion_effect": "zoom_out", "sound_effect_cue": "suspense_riser"},
                {"narration": "Dưới mặt đất, bước chân của chúa tể khiến muôn loài phải dè chừng.", "visual_keywords": "lion walking savanna", "motion_effect": "pan_right", "sound_effect_cue": "heartbeat"},
                {"narration": "Sức mạnh nguyên thủy bùng nổ làm chấn động toàn bộ không gian xung quanh.", "visual_keywords": "volcano eruption lava", "motion_effect": "ken_burns", "sound_effect_cue": "dramatic_boom"},
                {"narration": "Băng giá vĩnh cửu phản chiếu ánh sáng rực rỡ nơi tận cùng của thế giới.", "visual_keywords": "iceberg ocean arctic", "motion_effect": "zoom_in", "sound_effect_cue": "whoosh"},
                {"narration": "Đại dương sâu thẳm ẩn chứa những sinh vật khổng lồ đầy mê hoặc.", "visual_keywords": "whale ocean diving", "motion_effect": "pan_left", "sound_effect_cue": "suspense_riser"},
                {"narration": "Sự khéo léo và tốc độ hòa quyện tạo nên vẻ đẹp hoang dại phi thường.", "visual_keywords": "leopard tree wild", "motion_effect": "zoom_out", "sound_effect_cue": "camera_flash"},
                {"narration": "Và đó chính là lý do khiến thiên nhiên luôn là kiệt tác vĩ đại nhất.", "visual_keywords": "canyon sunset golden", "motion_effect": "ken_burns", "sound_effect_cue": "heartbeat"},
            ]

        for i, sc in enumerate(scenes):
            sc["scene_index"] = i
            sc["visual_prompt"] = f"Cinematic vertical 9:16 shot of {sc['visual_keywords']}, photorealistic 8k, volumetric dramatic lighting"
            sc["estimated_duration"] = 3.3

        script_dict = {
            "title": title,
            "description": desc,
            "hashtags": ["#shorts", "#fyp", "#viral", "#khampha", "#trending"],
            "hook": hook,
            "scenes": scenes,
            "call_to_action": cta,
        }
        return json.dumps(script_dict, ensure_ascii=False)

    async def _generate_ollama(
        self, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int
    ) -> str:
        live_env = self._get_live_env()
        base_url = live_env.get("OLLAMA_BASE_URL", settings.OLLAMA_BASE_URL).rstrip("/")
        configured_model = live_env.get("OLLAMA_MODEL", settings.OLLAMA_MODEL)

        # First verify Ollama is reachable and check installed models
        async with httpx.AsyncClient(timeout=4.0) as client:
            try:
                tag_res = await client.get(f"{base_url}/api/tags")
            except Exception as conn_err:
                raise RuntimeError(f"Ollama chưa chạy tại {base_url} ({conn_err})")

            if tag_res.status_code != 200:
                raise RuntimeError(f"Ollama trả về HTTP {tag_res.status_code}")

            installed = tag_res.json().get("models", [])
            if not installed:
                raise RuntimeError("Ollama đang chạy nhưng máy bạn CHƯA TẢI MODEL NÀO (danh sách models rỗng). Hãy mở CMD gõ: 'ollama run qwen2.5:1.5b'")

            # Check if configured model exists; if not, use the first available model
            model_names = [m.get("name", "") for m in installed]
            target_model = configured_model
            if not any(configured_model in name for name in model_names):
                target_model = model_names[0]
                logger.info(f"Configured model '{configured_model}' not found in Ollama. Auto-switching to '{target_model}'")

            # Call Ollama chat
            url = f"{base_url}/api/chat"
            payload = {
                "model": target_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                "stream": False,
                "format": "json",
                "keep_alive": live_env.get("OLLAMA_KEEP_ALIVE", "0s"),
            }

            logger.info(f"Calling Ollama model [{target_model}] at {url}...")
            res = await client.post(url, json=payload, timeout=120.0)
            if res.status_code != 200:
                raise RuntimeError(f"Ollama error (HTTP {res.status_code}): {res.text}")

            data = res.json()
            return data.get("message", {}).get("content", "")

    async def _generate_gemini(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        api_key: Optional[str] = None,
    ) -> str:
        live_env = self._get_live_env()
        key = api_key or live_env.get("GEMINI_API_KEY", settings.GEMINI_API_KEY)
        model = live_env.get("GEMINI_MODEL", settings.GEMINI_MODEL)
        if not key:
            raise ValueError("GEMINI_API_KEY is not configured in backend/.env")

        clean_model = model.strip().removeprefix("models/")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent"
            f"?key={key}"
        )
        headers = {"Content-Type": "application/json"}
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "responseMimeType": "application/json",
            },
        }

        models_to_try = [clean_model]
        for fallback_m in ["gemini-flash-lite-latest", "gemini-flash-latest"]:
            if fallback_m not in models_to_try:
                models_to_try.append(fallback_m)

        last_error = ""
        async with httpx.AsyncClient(timeout=60.0) as client:
            for m in models_to_try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
                logger.info(f"Calling Gemini model [{m}]...")
                try:
                    res = await client.post(url, json=payload, headers=headers)
                    if res.status_code == 200:
                        data = res.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "")
                    last_error = f"HTTP {res.status_code}: {res.text[:140]}"
                    logger.warning(f"Gemini model [{m}] returned {last_error}. Trying next fallback...")
                except Exception as req_err:
                    last_error = str(req_err)
                    logger.warning(f"Gemini request to [{m}] failed: {req_err}. Trying next fallback...")

        raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")


    async def _generate_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        api_key: Optional[str] = None,
    ) -> str:
        live_env = self._get_live_env()
        key = api_key or live_env.get("OPENAI_API_KEY", settings.OPENAI_API_KEY)
        base_url = live_env.get("OPENAI_BASE_URL", settings.OPENAI_BASE_URL).rstrip("/")
        model = live_env.get("OPENAI_MODEL", settings.OPENAI_MODEL)
        if not key:
            raise ValueError("OPENAI_API_KEY is not configured in backend/.env")

        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

        logger.info(f"Calling OpenAI model [{model}]...")
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(url, json=payload, headers=headers)
            if res.status_code != 200:
                raise RuntimeError(f"OpenAI error (HTTP {res.status_code}): {res.text}")

            data = res.json()
            return data["choices"][0]["message"]["content"]


llm_client = LLMClient()

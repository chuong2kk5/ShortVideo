import logging
import re
from pathlib import Path
from typing import Tuple, Optional, List
import httpx

from app.config import settings, BASE_DIR

logger = logging.getLogger("gemini_service")


def save_gemini_env_config(model: Optional[str] = None, api_key: Optional[str] = None) -> None:
    """Updates GEMINI_MODEL and/or GEMINI_API_KEY in backend/.env on disk."""
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return

    content = env_file.read_text(encoding="utf-8")

    def update_key(text: str, key: str, value: str) -> str:
        pattern = rf"^{key}=.*$"
        replacement = f"{key}={value}"
        if re.search(pattern, text, flags=re.MULTILINE):
            return re.sub(pattern, replacement, text, flags=re.MULTILINE)
        else:
            return text + f"\n{key}={value}"

    if model:
        content = update_key(content, "GEMINI_MODEL", model)
        settings.GEMINI_MODEL = model

    if api_key:
        content = update_key(content, "GEMINI_API_KEY", api_key)
        settings.GEMINI_API_KEY = api_key

    env_file.write_text(content, encoding="utf-8")
    logger.info(f"Updated backend/.env -> GEMINI_MODEL: {model or 'unchanged'}, GEMINI_API_KEY: {'configured' if api_key else 'unchanged'}")


async def auto_detect_gemini_model(
    api_key: str,
    preferred_model: Optional[str] = None,
) -> Tuple[bool, str, Optional[str]]:
    """
    Intelligently connects to Google Gemini API:
    1. Removes any 'models/' double-prefixes.
    2. Queries Google's ListModels API (v1beta and v1) to discover models active for this API key.
    3. Tests candidate models (gemini-1.5-flash, gemini-1.5-flash-latest, gemini-2.0-flash, etc.).
    4. Automatically binds to the first working model and updates backend/.env.
    """
    if not api_key or not api_key.strip():
        return False, "Vui lòng nhập GEMINI_API_KEY để kiểm tra!", None

    clean_key = api_key.strip()
    test_body = {
        "contents": [{"parts": [{"text": "Reply with 'OK'"}]}],
        "generationConfig": {"maxOutputTokens": 5},
    }
    headers = {"Content-Type": "application/json"}

    # 1. Candidate list
    candidates: List[str] = []
    if preferred_model and preferred_model.strip():
        clean_pref = preferred_model.strip().removeprefix("models/")
        if clean_pref:
            candidates.append(clean_pref)

    default_candidates = [
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-exp",
        "gemini-1.5-flash-002",
        "gemini-1.5-flash-001",
        "gemini-1.5-pro",
        "gemini-1.5-pro-latest",
        "gemini-pro",
    ]
    for dc in default_candidates:
        if dc not in candidates:
            candidates.append(dc)

    async with httpx.AsyncClient(timeout=12.0) as client:
        # 2. Try Google ListModels API to discover exact supported models
        discovered_models: List[str] = []
        for api_ver in ["v1beta", "v1"]:
            try:
                list_url = f"https://generativelanguage.googleapis.com/{api_ver}/models?key={clean_key}"
                l_res = await client.get(list_url)
                if l_res.status_code == 200:
                    models_data = l_res.json().get("models", [])
                    for m in models_data:
                        methods = m.get("supportedGenerationMethods", [])
                        if "generateContent" in methods:
                            m_name = m.get("name", "").removeprefix("models/")
                            if m_name and m_name not in discovered_models:
                                discovered_models.append(m_name)
                    if discovered_models:
                        logger.info(f"Discovered {len(discovered_models)} models supporting generateContent for this key ({api_ver}).")
                        break
            except Exception as e:
                logger.debug(f"ListModels failed for {api_ver}: {e}")

        # Prioritize discovered models (Flash first, then Pro)
        if discovered_models:
            def model_priority(name: str) -> int:
                nl = name.lower()
                if "2.0-flash" in nl:
                    return 0
                if "1.5-flash" in nl:
                    return 1
                if "flash" in nl:
                    return 2
                if "pro" in nl:
                    return 3
                return 4

            discovered_models.sort(key=model_priority)
            candidates = discovered_models + [c for c in candidates if c not in discovered_models]

        # 3. Test candidate models
        last_error = ""
        for model_name in candidates:
            for api_ver in ["v1beta", "v1"]:
                url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_name}:generateContent?key={clean_key}"
                try:
                    res = await client.post(url, json=test_body, headers=headers)
                    if res.status_code == 200:
                        save_gemini_env_config(model=model_name, api_key=clean_key)
                        logger.info(f"Successfully verified Gemini model [{model_name}] on API version [{api_ver}].")
                        return (
                            True,
                            f"Kết nối Gemini API thành công! Đã tự động kích hoạt model '{model_name}' ({api_ver}).",
                            model_name,
                        )
                    elif res.status_code == 400:
                        err_data = res.json().get("error", {})
                        msg = err_data.get("message", res.text[:200])
                        last_error = msg
                        if "API key not valid" in msg:
                            return False, f"API Key không hợp lệ: {msg}", None
                    else:
                        err_data = res.json().get("error", {})
                        last_error = err_data.get("message", res.text[:200])
                except Exception as ex:
                    last_error = str(ex)

        # 4. If none worked
        return (
            False,
            (
                f"Gemini API báo lỗi: {last_error}\n\n"
                f"Nguyên nhân: API Key này hiện chưa được kích hoạt model sinh văn bản hoặc bị giới hạn quyền.\n"
                f"👉 Khắc phục nhanh: Hãy truy cập https://aistudio.google.com/app/apikey tạo 1 API Key mới miễn phí và dán vào đây."
            ),
            None,
        )


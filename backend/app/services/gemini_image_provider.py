import base64
import logging
from pathlib import Path
from typing import Optional
import httpx
from dotenv import dotenv_values
from app.config import settings, BASE_DIR

logger = logging.getLogger("gemini_image_provider")


class GeminiImageProvider:
    """
    Generates photorealistic 9:16 vertical images using Google Imagen 3
    via the Gemini REST API.
    """

    def _get_live_gemini_key(self) -> Optional[str]:
        """Reads GEMINI_API_KEY fresh from backend/.env so users don't have to restart the server."""
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            vals = dotenv_values(str(env_file))
            k = vals.get("GEMINI_API_KEY", "").strip()
            if k:
                return k
        return settings.GEMINI_API_KEY.strip() or None

    async def generate_image(
        self,
        prompt: str,
        output_path: Path,
    ) -> Optional[Path]:
        """
        Calls Google Imagen 3 API with 9:16 vertical aspect ratio.
        """
        api_key = self._get_live_gemini_key()
        if not api_key:
            logger.debug("GEMINI_API_KEY not configured. Skipping Gemini Imagen.")
            return None

        # Clean prompt - remove negative instructions or excessive length
        clean_prompt = prompt.strip()
        if len(clean_prompt) > 400:
            clean_prompt = clean_prompt[:400]

        models_to_try = [
            "imagen-3.0-generate-002",
            "imagen-3.0-generate-001",
        ]

        headers = {"Content-Type": "application/json"}
        payload = {
            "instances": [
                {
                    "prompt": f"{clean_prompt}, cinematic vertical 9:16 composition, ultra photorealistic, 8k resolution, dramatic cinematic lighting, award-winning photography",
                }
            ],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "9:16",
                "outputMimeType": "image/jpeg",
            },
        }

        for model_name in models_to_try:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:predict"
                f"?key={api_key}"
            )
            try:
                logger.info(f"Calling Google Imagen model [{model_name}] for prompt: '{clean_prompt[:60]}...'")
                async with httpx.AsyncClient(timeout=45.0) as client:
                    res = await client.post(url, json=payload, headers=headers)
                    if res.status_code == 200:
                        data = res.json()
                        predictions = data.get("predictions", [])
                        if predictions and "bytesBase64Encoded" in predictions[0]:
                            b64_data = predictions[0]["bytesBase64Encoded"]
                            img_bytes = base64.b64decode(b64_data)
                            output_path.parent.mkdir(parents=True, exist_ok=True)
                            output_path.write_bytes(img_bytes)
                            logger.info(
                                f"Google Imagen [{model_name}] image saved to {output_path} ({len(img_bytes)} bytes)"
                            )
                            return output_path
                    else:
                        logger.warning(
                            f"Google Imagen [{model_name}] returned HTTP {res.status_code}: {res.text[:150]}"
                        )
            except Exception as e:
                logger.warning(f"Error calling Google Imagen [{model_name}]: {e}")

        return None


gemini_image_provider = GeminiImageProvider()

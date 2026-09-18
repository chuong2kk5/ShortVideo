import json
import logging
import re
from typing import Type, TypeVar, Tuple, Optional, Callable, Awaitable
from pydantic import BaseModel, ValidationError
from app.orchestrator.prompt_templates import (
    VIRAL_SHORTS_SYSTEM_PROMPT,
    build_json_repair_prompt,
)

logger = logging.getLogger("json_repair")

T = TypeVar("T", bound=BaseModel)


def extract_json_from_text(raw_text: str) -> str:
    """
    Strips markdown code fences and isolates the outermost valid JSON object/array.
    """
    if not raw_text:
        return ""

    text = raw_text.strip()

    # 1. Strip Markdown fences like ```json ... ``` or ``` ... ```
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(fence_pattern, text)
    if match:
        text = match.group(1).strip()

    # 2. Extract substring between first '{' and last '}'
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        text = text[first_brace : last_brace + 1]

    return text


class SelfHealingJSONValidator:
    """
    Validates JSON strings against Pydantic schemas.
    If validation or syntax fails, automatically queries LLM with detailed
    validation error logs to repair and recover the JSON (up to max_retries times).
    """

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def parse_and_validate(self, raw_text: str, schema_cls: Type[T]) -> Tuple[Optional[T], Optional[str]]:
        """
        Attempts to parse and validate text into schema_cls.
        Returns (validated_instance, error_message).
        """
        cleaned = extract_json_from_text(raw_text)
        if not cleaned:
            return None, "Empty text or no JSON object found in response."

        try:
            # First try standard json parsing with non-strict mode
            data = json.loads(cleaned, strict=False)
        except Exception as jde:
            try:
                import json_repair
                data = json_repair.loads(cleaned)
                if not isinstance(data, dict):
                    return None, f"JSON Syntax Error: Repaired output is not a JSON object: {jde}"
            except Exception as repair_err:
                return None, f"JSON Syntax Error: {jde} (Auto-repair failed: {repair_err})"

        try:
            instance = schema_cls.model_validate(data)
            return instance, None
        except ValidationError as ve:
            # Format readable error messages
            error_details = []
            for err in ve.errors():
                loc = " -> ".join(str(p) for p in err.get("loc", []))
                msg = err.get("msg", "")
                error_details.append(f"Field '{loc}': {msg}")
            return None, "\n".join(error_details)

    async def execute_with_self_healing(
        self,
        initial_raw_text: str,
        schema_cls: Type[T],
        llm_generate_fn: Callable[[str, str], Awaitable[str]],
        system_prompt: str = VIRAL_SHORTS_SYSTEM_PROMPT,
    ) -> T:
        """
        Executes schema validation with an automatic retry loop (up to max_retries).
        """
        current_text = initial_raw_text
        last_error = ""

        for attempt in range(1, self.max_retries + 1):
            logger.info(f"Pydantic validation attempt #{attempt} for schema '{schema_cls.__name__}'...")
            instance, error_msg = self.parse_and_validate(current_text, schema_cls)

            if instance is not None:
                logger.info(f"JSON validation SUCCEEDED on attempt #{attempt}.")
                return instance

            last_error = error_msg or "Unknown schema error"
            logger.warning(
                f"JSON Validation failed on attempt #{attempt}/{self.max_retries}. "
                f"Errors:\n{last_error}"
            )

            if attempt < self.max_retries:
                repair_prompt = build_json_repair_prompt(
                    invalid_json_text=current_text,
                    validation_errors=last_error,
                )
                logger.info("Invoking LLM for self-healing JSON correction...")
                try:
                    current_text = await llm_generate_fn(system_prompt, repair_prompt)
                except Exception as e:
                    logger.error(f"Error during LLM self-healing call: {e}")
                    raise RuntimeError(f"Self-healing LLM call failed: {e}")

        raise ValueError(
            f"Failed to obtain valid JSON conforming to {schema_cls.__name__} after "
            f"{self.max_retries} attempts. Last error:\n{last_error}\nRaw output:\n{current_text[:500]}"
        )


json_validator = SelfHealingJSONValidator(max_retries=3)


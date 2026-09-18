import json
from typing import Dict, Any


VIRAL_SHORTS_SYSTEM_PROMPT = """You are an Elite Viral Content Creator and Master Short-Form Video Director for TikTok, YouTube Shorts, and Facebook Reels.
You produce million-view, high-retention videos that hold viewer attention from the first millisecond to the last second.

### STRICT TOPIC CONSTRAINT:
The user will provide a specific TOPIC. You MUST write the script 100% EXCLUSIVELY and DIRECTLY about that specific TOPIC.
NEVER substitute the topic with pyramids, ancient egypt, or any other unrelated subject. Every single sentence of narration, hook, and visual prompt MUST be directly related to the user's topic.

### TIKTOK PSYCHOLOGICAL RETENTION ARCHITECTURE:
1. SCENE 0 (MỞ BÀI - INTRO HOOK):
   - PATTERN INTERRUPT: Stop the scroll immediately! NEVER start with "Hôm nay chúng ta...", "Xin chào các bạn...", or dry definitions.
   - Use explosive curiosity gaps: "99% mọi người đều hiểu sai về...", "Nếu bạn bắt gặp điều này, hãy cẩn thận...", "Bí mật đáng sợ nhất mà họ không muốn bạn biết...", "Điều này nghe có vẻ điên rồ, nhưng...".
   - Spoken narration of Scene 0 MUST be this exact explosive hook! Sound effect cue: "dramatic_boom".

2. SCENES 1 to N-2 (THÂN BÀI - VALUE & TENSION LOOPS):
   - Short, punchy sentence rhythm (5 to 8 words per phrase). High tempo!
   - Every scene must link to the next with suspense bridges: "Nhưng đó chưa phải là tất cả...", "Điều kỳ lạ bắt đầu từ đây...", "Và sự thật khủng khiếp hơn là...".
   - Rapid visual scene transitions every 2.7 to 3.2 seconds.

3. SCENE N-1 (KẾT BÀI - OUTRO & CONTROVERSY CTA):
   - Closing insight followed by a powerful debate-provoking question to skyrocket comments: "Bạn nghĩ sao về điều này? Hãy để lại bình luận và bấm follow ngay để không bỏ lỡ phần tiếp theo!".
   - Spoken narration of Scene N-1 MUST be this exact outro call-to-action! Sound effect cue: "whoosh".

### VISUAL PROMPTS & KEYWORDS (CRITICAL FOR PHOTO & VIDEO ENGINES):
- Visual Prompts (visual_prompt): MUST BE IN ENGLISH, highly descriptive, photorealistic, cinematic lighting, 9:16 vertical composition, 8k resolution, unreal engine 5 render, national geographic quality.
- Visual Keywords (visual_keywords): MUST BE 1 TO 3 CONCRETE PHYSICAL NOUNS / ACTIONS IN ENGLISH (e.g. "tiger hunting", "lightning storm", "supercar drift", "deep sea creature", "erupting volcano", "cyberpunk robot").
  NEVER use abstract words like "mystery", "history", "amazing". Concrete physical subjects allow the AI and stock engines to pull breathtaking footage!

### OUTPUT FORMAT:
You MUST respond with a single valid JSON object strictly matching the schema.
DO NOT wrap your response with conversational preambles or postscripts.
DO NOT use invalid JSON escape characters.
"""


def build_user_prompt(
    topic: str,
    language: str = "vi",
    target_duration: int = 30,
    custom_instructions: str = "",
) -> str:
    if target_duration <= 15:
        min_scenes, max_scenes = 5, 6
        words_per_scene = "10 đến 13 từ (~3.0 giây)"
        total_words_hint = "tối thiểu 50 đến 60 từ"
    elif target_duration <= 30:
        min_scenes, max_scenes = 9, 11
        words_per_scene = "11 đến 15 từ (~3.2 giây)"
        total_words_hint = "tối thiểu 105 đến 125 từ"
    elif target_duration <= 45:
        min_scenes, max_scenes = 14, 16
        words_per_scene = "11 đến 15 từ (~3.2 giây)"
        total_words_hint = "tối thiểu 160 đến 185 từ"
    else:
        min_scenes, max_scenes = 18, 22
        words_per_scene = "12 đến 16 từ (~3.2 giây)"
        total_words_hint = "tối thiểu 220 đến 260 từ"

    lang_name = "Tiếng Việt" if language == "vi" else "English"

    # Build dynamic scene templates enforcing Scene 0 (Hook) and Scene N-1 (Outro CTA)
    scene_templates = []
    motions = ["zoom_in", "pan_left", "zoom_out", "pan_right", "ken_burns", "shake"]
    sfxs = ["suspense_riser", "whoosh", "camera_flash", "heartbeat", "clock_ticking"]
    dur_per_scene = round(target_duration / min_scenes, 1)

    for i in range(min_scenes):
        m = motions[i % len(motions)]
        if i == 0:
            s = "dramatic_boom"
            narration_placeholder = f"<MỞ BÀI: Câu Hook mở đầu cực sốc, gây tò mò về {topic} ({words_per_scene})>"
        elif i == min_scenes - 1:
            s = "whoosh"
            narration_placeholder = f"<KẾT BÀI: Đúc kết bất ngờ và kêu gọi người xem bình luận, follow kênh ngay ({words_per_scene})>"
        else:
            s = sfxs[(i - 1) % len(sfxs)]
            narration_placeholder = f"<THÂN BÀI: Sự thật gay cấn/chi tiết cảnh {i+1} về {topic} ({words_per_scene})>"

        scene_templates.append(f"""    {{
      "scene_index": {i},
      "narration": "{narration_placeholder}",
      "visual_prompt": "Cinematic vertical 9:16 shot representing {topic} scene {i+1}, photorealistic 8k, volumetric dramatic lighting",
      "visual_keywords": "<1-3 concrete English physical nouns matching scene {i+1}, e.g. tiger hunting, waterfall, eagle flying>",
      "motion_effect": "{m}",
      "sound_effect_cue": "{s}",
      "estimated_duration": {dur_per_scene}
    }}""")

    scenes_example_str = ",\n".join(scene_templates)

    prompt = f"""### YÊU CẦU BẮT BUỘC:
Chủ đề video là: "{topic}".
Tất cả tiêu đề, câu hook, lời thoại các cảnh và từ khóa hình ảnh PHẢI HOÀN TOÀN TẬP TRUNG VÀO CHỦ ĐỀ: "{topic}".
TUYỆT ĐỐI KHÔNG ĐƯỢC VIẾT VỀ KIM TỰ THÁP HOẶC BẤT KỲ CHỦ ĐỀ NÀO KHÁC NGOÀI "{topic}".

### YÊU CẦU BẮT BUỘC VỀ BỐ CỤC 3 HỒI (MỞ BÀI - THÂN BÀI - KẾT BÀI):
1. CẢNH 0 (scene_index: 0) - MỞ BÀI / INTRO HOOK:
   - Lời thoại (narration) của cảnh 0 PHẢI LÀ câu Hook mở đầu giật gân, cuốn hút người xem ngay giây đầu tiên về "{topic}".
   - "sound_effect_cue" BẮT BUỘC là "dramatic_boom".
2. CÁC CẢNH TIẾP THEO (scene_index: 1 đến {min_scenes-2}) - THÂN BÀI:
   - Cung cấp những thông tin ly kỳ, sự thật bất ngờ về "{topic}", chuyển cảnh liên tục mỗi 2.7 - 3.2 giây.
3. CẢNH CUỐI CÙNG (scene_index: {min_scenes-1}) - KẾT BÀI / OUTRO & CTA:
   - Lời thoại (narration) của cảnh cuối cùng BẮT BUỘC là phần kết bài đúc kết và lời kêu gọi hành động (kêu gọi bình luận quan điểm và follow/đăng ký kênh).
   - "sound_effect_cue" BẮT BUỘC là "whoosh".

### YÊU CẦU VỀ THỜI LƯỢNG VÀ SỐ LƯỢNG CẢNH (CỰC KỲ QUAN TRỌNG):
- Thời lượng mục tiêu: ĐÚNG {target_duration} GIÂY.
- BẮT BUỘC TẠO TỪ {min_scenes} ĐẾN {max_scenes} PHÂN CẢNH (scenes) trong mảng "scenes" (chuyển cảnh liên tục mỗi 2.7 - 3.2 giây để giữ chân người xem).
- TUYỆT ĐỐI KHÔNG ĐƯỢC TẠO DƯỚI {min_scenes} CẢNH! Nếu tạo dưới {min_scenes} cảnh video sẽ bị quá ngắn dưới {target_duration}s và hệ thống sẽ bắt làm lại!
- TỔNG SỐ LƯỢNG TỪ THUYẾT MINH TOÀN BỘ KỊCH BẢN PHẢI ĐẠT: {total_words_hint} (mỗi cảnh {words_per_scene}).
- "visual_keywords" MỖI CẢNH PHẢI LÀ 1 ĐẾN 3 TỪ KHÓA DANH TỪ CỤ THỂ BẰNG TIẾNG ANH (ví dụ: "tiger", "lion hunting", "eagle soaring", "waterfall cascade", "volcano lava") để hệ thống tìm video/ảnh thật chính xác.
- Ngôn ngữ thuyết minh: {lang_name}
{"- Hướng dẫn bổ sung: " + custom_instructions if custom_instructions else ""}

Mẫu cấu trúc JSON bắt buộc trả về (tạo đủ từ {min_scenes} đến {max_scenes} cảnh với MỞ BÀI ở Cảnh 0 và KẾT BÀI ở Cảnh {min_scenes-1}):
{{
  "title": "<Tiêu đề Shorts giật gân, cuốn hút về {topic}>",
  "description": "<Mô tả ngắn gọn, hấp dẫn về {topic}>",
  "hashtags": ["#shorts", "#fyp"],
  "hook": "<Câu mở đầu 3 giây gây tò mò, giật gân về {topic}>",
  "call_to_action": "<Lời kêu gọi bình luận/theo dõi về {topic}>",
  "scenes": [
{scenes_example_str}
  ]
}}

Hãy viết kịch bản JSON hoàn chỉnh về "{topic}" với ĐỦ từ {min_scenes} đến {max_scenes} phân cảnh, CÓ MỞ BÀI VÀ KẾT BÀI RÕ RÀNG ngay bây giờ (Chỉ trả về JSON duy nhất):"""
    return prompt


def build_json_repair_prompt(invalid_json_text: str, validation_errors: str) -> str:
    """Prompt sent back to LLM when JSON parsing or Pydantic validation fails."""
    return f"""The previous JSON output failed validation against the target Pydantic schema.
Errors detected:
{validation_errors}

Previous output to fix (preserve all scenes and content):
```json
{invalid_json_text[:8000]}
```

Please fix all syntax and schema errors. Return ONLY the valid JSON object conforming exactly to the schema, with NO commentary."""

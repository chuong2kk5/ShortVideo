import json
import re
from typing import Dict, Any, Optional

CONTENT_STYLE_DIRECTIVES: Dict[str, str] = {
    "storytelling_drama": (
        "PHONG CÁCH KỂ CHUYỆN DRAMA (Storytelling / Emotional Arc):\n"
        "- Dẫn dắt như một câu chuyện có chiều sâu: giới thiệu nhân vật/bối cảnh, cao trào mâu thuẫn hoặc bước ngoặt kịch tính, và bài học đắt giá.\n"
        "- Lời thoại giàu tính miêu tả, tạo cảm xúc chân thực, cuốn hút người nghe như đang xem một tập phim ngắn."
    ),
    "top_facts": (
        "PHONG CÁCH DANH SÁCH / TOP SỰ THẬT (Rapid-Fire Countdown):\n"
        "- Nhịp độ dồn dập, tiết lộ các chi tiết kinh ngạc hoặc sự thật ít ai biết theo từng cảnh.\n"
        "- Mỗi cảnh là một phát hiện độc lập, sắc bén, kích thích người xem xem tiếp cảnh sau."
    ),
    "mystery_curiosity": (
        "PHONG CÁCH KỲ BÍ / HỒI HỘP (Mystery & Unexplained Phenomena):\n"
        "- Xây dựng không khí bí ẩn, đặt ra những câu hỏi chưa có lời giải đáp.\n"
        "- Tiết lộ từng manh mối ly kỳ, đẩy trí tò mò của người xem lên tột đỉnh."
    ),
    "educational": (
        "PHONG CÁCH KHÁM PHÁ & KHOA HỌC ĐỜI SỐNG (Illuminating Explainer):\n"
        "- Biến kiến thức phức tạp thành những ví dụ đời thường, dễ hiểu, trực quan và hấp dẫn.\n"
        "- Kết thúc bằng góc nhìn mới mẻ giúp người xem cảm thấy 'học được điều gì đó giá trị'."
    ),
}

ART_STYLE_DIRECTIVES: Dict[str, str] = {
    "cinematic": (
        "Cinematic 35mm film photography, Panavision lens, photorealistic 8k, volumetric dramatic lighting, "
        "shallow depth of field, hyper-detailed, award-winning national geographic photography"
    ),
    "3d_animation": (
        "Pixar and Disney 3D animation style, adorable and expressive characters, Octane Render, "
        "vibrant warm lighting, ray tracing, cute ultra-detailed, playful masterpiece"
    ),
    "anime_ghibli": (
        "Studio Ghibli and Makoto Shinkai anime aesthetic, lush hand-painted scenery, vibrant colors, "
        "atmospheric sunlight, nostalgic emotional anime art, masterpiece"
    ),
    "dark_mystery": (
        "Chiaroscuro noir lighting, atmospheric deep fog, ominous shadows, high contrast, "
        "cinematic suspense, moody 8k masterpiece, photorealistic"
    ),
    "historic_painting": (
        "Classical oil painting masterpiece, golden ratio composition, rich museum oil canvas texture, "
        "epic historical realism, dramatic Rembrandt lighting"
    ),
}


def resolve_art_style(topic: str, requested_style: Optional[str] = "auto") -> str:
    """Detects or returns the best visual art style preset."""
    if requested_style and requested_style.lower() in ART_STYLE_DIRECTIVES:
        return requested_style.lower()

    t_lower = topic.lower()
    if any(k in t_lower for k in ["anime", "manga", "ghibli", "hoạt hình nhật", "naruto", "wibu"]):
        return "anime_ghibli"
    if any(k in t_lower for k in ["3d", "pixar", "disney", "hoạt hình 3d", "dễ thương", "cổ tích", "thiếu nhi", "hoạt họa"]):
        return "3d_animation"
    if any(k in t_lower for k in ["bí ẩn", "kinh dị", "rùng rợn", "ma quái", "đáy biển sâu", "vực thẳm", "quái vật", "bóng tối"]):
        return "dark_mystery"
    if any(k in t_lower for k in ["lịch sử", "cổ đại", "thời xưa", "vua chúa", "triều đại", "la mã", "phục hưng", "chiến tranh thế giới"]):
        return "historic_painting"
    return "cinematic"


def resolve_content_style(topic: str, requested_style: Optional[str] = "auto") -> str:
    """Detects or returns the best narrative content archetype."""
    if requested_style and requested_style.lower() in CONTENT_STYLE_DIRECTIVES:
        return requested_style.lower()

    t_lower = topic.lower()
    if any(k in t_lower for k in ["top", "những", "sự thật", "điều", "danh sách", "lý do"]):
        return "top_facts"
    if any(k in t_lower for k in ["bí ẩn", "tại sao", "vì sao", "hiện tượng", "chưa có lời giải", "kỳ lạ"]):
        return "mystery_curiosity"
    if any(k in t_lower for k in ["cách", "hướng dẫn", "nguyên lý", "khoa học", "bài học", "bản chất"]):
        return "educational"
    return "storytelling_drama"


VIRAL_SHORTS_SYSTEM_PROMPT = """You are an Elite Viral Content Creator and Master Short-Form Video Director for TikTok, YouTube Shorts, and Facebook Reels.
You produce million-view, high-retention videos that hold viewer attention from the first millisecond to the last second.

### STRICT TOPIC CONSTRAINT:
The user will provide a specific TOPIC. You MUST write the script 100% EXCLUSIVELY and DIRECTLY about that specific TOPIC.
NEVER substitute the topic with pyramids, ancient egypt, or any unrelated subject.

### IMMERSIVE STORYTELLING MASTERY (KỂ CHUYỆN NHẬP VAI - TUYỆT ĐỐI KHÔNG TẢ VĂN GIÁO KHOA):
1. KHÔNG VIẾT KIỂU TẢ VĂN / ĐỊNH NGHĨA KHÔ KHAN:
   - TUYỆT ĐỐI KHÔNG dùng các câu thuyết minh sáo rỗng, nhận định trừu tượng như: "Khoa học hiện đại vẫn chưa thể giải thích nổi...", "Các chuyên gia đã vô cùng kinh ngạc...", "Nơi đây có khí hậu khắc nghiệt và nhiều điều bí ẩn...".
   - Tuyệt đối TRÁNH các câu văn mẫu sáo rỗng bị lặp đi lặp lại như: "99% mọi người đều hiểu sai về...", "Bí mật đáng sợ nhất mà họ không muốn bạn biết...", "Điều này nghe có vẻ điên rồ...".

2. KỂ CHUYỆN CÓ CỐT TRUYỆN, NHÂN VẬT & DIỄN BIẾN LE TĂNG (STORY ARC):
   - Mở màn bằng một biến cố giật gân, nhân vật thực tế, hoặc tình huống đưa người xem trực tiếp vào vai người trải nghiệm.
   - Từng phân cảnh là một bước phát triển kịch tính tiếp nối của câu chuyện (hành động nhân vật, khám phá nguy hiểm, tiếng động kỳ lạ, bước ngoặt sốc).
   - Tận dụng tối đa chi tiết giác quan (tiếng la bàn quay cuồng, bóng đen vụt qua cây cổ thụ, tiếng thì thầm trong sương đêm, vết rách trên lều...).

3. CẤM LẶP LẠI NGUYÊN VĂN TÊN CHỦ ĐỀ TRONG LỜI THOẠI (STRICT ANTI-TOPIC-REPETITION):
   - TUYỆT ĐỐI KHÔNG chèn nguyên văn cụm từ chủ đề vào giữa câu thoại (ví dụ cấm nói: "xảy ra tại những vụ mất tích bí ẩn trong rừng amazon").
   - Hãy dùng ngôn ngữ tự nhiên: "vùng đất chết này", "chuyến thám hiểm định mệnh", "họ", "đoàn người", "con quái vật", "nơi đây"...

4. KHẨU NGỮ TỰ NHIÊN & ĐIỂM RƠI NHỊP ĐIỆU (SPOKEN VIETNAMESE CADENCE):
   - Sử dụng ngôn từ nói chuyện đời thường, truyền cảm, có hồn, giàu hình ảnh.
   - Ngắt câu nhịp nhàng (5 đến 8 từ một vế câu). Sử dụng dấu phẩy (,), dấu chấm (.), dấu ba chấm (...) khéo léo để giọng đọc AI ngắt nghỉ tự nhiên, có điểm rơi nhịp điệu (cadence).

### VISUAL PROMPTS & KEYWORDS (100% TIED TO STORY ACTION):
- Visual Prompts (visual_prompt): MUST BE 100% IN ENGLISH, highly descriptive, cinematic lighting, 9:16 vertical composition, 8k resolution, tailored to the requested Art Style.
  - MUST depict the EXACT PHYSICAL STORY ACTION occurring in THAT scene (e.g. "British explorer in 1920s gear holding lantern trekking through dark foggy rainforest vines", "Close up of torn expedition tent flapping violently in stormy jungle wind").
  - NEVER use generic abstract props like "magnifying glass on desk", "paper map on table", "scientist office" unless the topic is literally an office desk! Show the actual jungle, space, animals, ocean, or characters!
- Visual Keywords (visual_keywords): MUST BE 2 TO 4 CONCRETE PHYSICAL ENGLISH NOUNS (e.g. "rainforest explorer lantern", "abandoned campsite rain", "dense jungle mist night", "ancient stone ruins").
  NEVER use abstract words like "mystery", "history", "amazing". Concrete physical subjects allow the AI engines to render breathtaking footage!

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
    content_style: str = "auto",
    art_style: str = "auto",
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

    resolved_c_style = resolve_content_style(topic, content_style)
    content_directive = CONTENT_STYLE_DIRECTIVES.get(resolved_c_style, CONTENT_STYLE_DIRECTIVES["storytelling_drama"])

    resolved_a_style = resolve_art_style(topic, art_style)
    art_style_prompt_suffix = ART_STYLE_DIRECTIVES.get(resolved_a_style, ART_STYLE_DIRECTIVES["cinematic"])

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
            narration_placeholder = f"<MỞ BÀI: Câu Hook giật gân, cuốn người xem ngay lập tức vào câu chuyện ({words_per_scene})>"
        elif i == min_scenes - 1:
            s = "whoosh"
            narration_placeholder = f"<KẾT BÀI: Đúc kết bất ngờ và kêu gọi người xem bình luận, follow kênh ngay ({words_per_scene})>"
        else:
            s = sfxs[(i - 1) % len(sfxs)]
            narration_placeholder = f"<THÂN BÀI CẢNH {i+1}: Diễn biến kịch tính tiếp theo của câu chuyện, hành động cụ thể ({words_per_scene})>"

        scene_templates.append(f"""    {{
      "scene_index": {i},
      "narration": "{narration_placeholder}",
      "visual_prompt": "Vertical 9:16 cinematic shot showing concrete story action of scene {i+1}, {art_style_prompt_suffix}",
      "visual_keywords": "<2-4 concrete English physical nouns matching this exact scene's action>",
      "motion_effect": "{m}",
      "sound_effect_cue": "{s}",
      "estimated_duration": {dur_per_scene}
    }}""")

    scenes_example_str = ",\n".join(scene_templates)

    prompt = f"""### YÊU CẦU BẮT BUỘC:
Chủ đề video là: "{topic}".
Tất cả tiêu đề, câu hook, câu chuyện kịch bản và hình ảnh PHẢI HOÀN TOÀN TẬP TRUNG VÀO: "{topic}".

### NGUYÊN TẮC STORYTELLING ĐỈNH CAO (QUAN TRỌNG NHẤT):
- KỂ CHUYỆN NHẬP VAI, KHÔNG TẢ VĂN: Xây dựng câu chuyện có diễn biến liên tục, từng cảnh là một bước phát triển hấp dẫn, lôi cuốn người nghe theo dõi đến giây cuối cùng.
- CẤM LẶP LẠI TÊN CHỦ ĐỀ: TUYỆT ĐỐI KHÔNG lặp lại cụm từ "{topic}" trong lời thoại các cảnh thân bài! Dùng ngôn ngữ tự nhiên: "nơi này", "họ", "đoàn người", "chuyến đi định mệnh"...
- CẤM CÂU THUYẾT MINH CHUNG CHUNG: Cấm các câu sáo rỗng như "khoa học chưa giải thích nổi", "các chuyên gia kinh ngạc". Mọi cảnh phải có chi tiết hành động hoặc sự kiện cụ thể!

### ĐỊNH HƯỚNG NỘI DUNG & PHONG CÁCH KỊCH BẢN:
{content_directive}

### ĐỊNH HƯỚNG PHONG CÁCH THẨM MỸ HÌNH ẢNH (ART STYLE):
Phong cách hình ảnh áp dụng đồng bộ cho tất cả các cảnh: [{resolved_a_style}]
Visual Prompt mỗi cảnh phải kết thúc bằng phong cách này: "{art_style_prompt_suffix}"
Mỗi cảnh PHẢI MÔ TẢ ĐÚNG HÀNH ĐỘNG THỰC TẾ của phân cảnh đó (CẤM vẽ kính lúp bàn làm việc trừu tượng khi kể về thiên nhiên, rừng rậm hay vũ trụ).

### YÊU CẦU BẮT BUỘC VỀ BỐ CỤC 3 HỒI (MỞ BÀI - THÂN BÀI - KẾT BÀI):
1. CẢNH 0 (scene_index: 0) - MỞ BÀI / INTRO HOOK:
   - Lời thoại (narration) của cảnh 0 PHẢI LÀ câu Hook mở đầu kích thích tò mò cực độ về câu chuyện.
   - Tuyệt đối không dùng văn mẫu sáo rỗng ("99% mọi người...").
   - "sound_effect_cue" BẮT BUỘC là "dramatic_boom".
2. CÁC CẢNH TIẾP THEO (scene_index: 1 đến {min_scenes-2}) - THÂN BÀI:
   - Diễn biến dồn dập, căng thẳng leo thang, chuyển cảnh liên tục mỗi 2.7 - 3.2 giây.
3. CẢNH CUỐI CÙNG (scene_index: {min_scenes-1}) - KẾT BÀI / OUTRO & CTA:
   - Lời thoại (narration) của cảnh cuối cùng BẮT BUỘC là phần kết bài đúc kết bất ngờ và kêu gọi hành động (bình luận và follow kênh).
   - "sound_effect_cue" BẮT BUỘC là "whoosh".

### YÊU CẦU VỀ THỜI LƯỢNG VÀ SỐ LƯỢNG CẢNH (CỰC KỲ QUAN TRỌNG):
- Thời lượng mục tiêu: ĐÚNG {target_duration} GIÂY.
- BẮT BUỘC TẠO TỪ {min_scenes} ĐẾN {max_scenes} PHÂN CẢNH (scenes) trong mảng "scenes".
- TUYỆT ĐỐI KHÔNG ĐƯỢC TẠO DƯỚI {min_scenes} CẢNH!
- TỔNG SỐ LƯỢNG TỪ THUYẾT MINH TOÀN BỘ KỊCH BẢN PHẢI ĐẠT: {total_words_hint} (mỗi cảnh {words_per_scene}).
- "visual_keywords" MỖI CẢNH PHẢI LÀ 2 ĐẾN 4 TỪ KHÓA DANH TỪ CỤ THỂ BẰNG TIẾNG ANH mô tả đúng hành động của cảnh đó.
- Ngôn ngữ thuyết minh: {lang_name}
{"- Hướng dẫn bổ sung: " + custom_instructions if custom_instructions else ""}

Mẫu cấu trúc JSON bắt buộc trả về (tạo đủ từ {min_scenes} đến {max_scenes} cảnh với MỞ BÀI ở Cảnh 0 và KẾT BÀI ở Cảnh {min_scenes-1}):
{{
  "title": "<Tiêu đề Shorts giật gân, cuốn hút>",
  "description": "<Mô tả ngắn gọn, hấp dẫn>",
  "hashtags": ["#shorts", "#fyp"],
  "hook": "<Câu mở đầu sắc bén gây tò mò>",
  "call_to_action": "<Lời kêu gọi bình luận/theo dõi>",
  "scenes": [
{scenes_example_str}
  ]
}}

Hãy viết kịch bản JSON hoàn chỉnh với ĐỦ từ {min_scenes} đến {max_scenes} phân cảnh theo lối STORYTELLING LÔI CUỐN ngay bây giờ (Chỉ trả về JSON duy nhất):"""
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

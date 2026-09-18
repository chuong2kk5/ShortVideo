import asyncio
from app.orchestrator.llm_client import llm_client

sys_prompt = """You are an elite YouTube Shorts Director. You write viral, psychological, highly engaging short scripts.
CRITICAL RULE: You MUST write the script EXCLUSIVELY about the user's requested topic. NEVER write about ancient pyramids or unrelated subjects.
Output strictly valid JSON with no conversational preambles or markdown."""

topic = "Thiên nhiên hoang dã kỳ vĩ"
user_prompt = f"""YÊU CẦU QUAN TRỌNG NHẤT:
Chủ đề video là: "{topic}".
Tất cả tiêu đề, câu hook, lời thoại, và hình ảnh PHẢI HOÀN TOÀN NÓI VỀ "{topic}". TUYỆT ĐỐI KHÔNG NÓI VỀ KIM TỰ THÁP HAY CHỦ ĐỀ KHÁC.

Mẫu cấu trúc JSON bắt buộc:
{{
  "title": "<Tiêu đề giật gân, cuốn hút về {topic}>",
  "description": "<Mô tả ngắn gọn về {topic}>",
  "hashtags": ["#shorts", "#fyp"],
  "hook": "<Câu mở đầu 3 giây gây tò mò về {topic}>",
  "scenes": [
    {{
      "scene_index": 0,
      "narration": "<Lời thoại thuyết minh cảnh 1 về {topic}>",
      "visual_prompt": "Cinematic vertical 9:16 shot of wild nature landscapes, photorealistic 8k",
      "visual_keywords": "wildlife nature safari animals",
      "motion_effect": "zoom_in",
      "sound_effect_cue": "whoosh",
      "estimated_duration": 4.0
    }},
    {{
      "scene_index": 1,
      "narration": "<Lời thoại thuyết minh cảnh 2 về {topic}>",
      "visual_prompt": "Cinematic vertical 9:16 shot of pristine jungle waterfall, dramatic lighting",
      "visual_keywords": "wild jungle rainforest nature",
      "motion_effect": "pan_left",
      "sound_effect_cue": "dramatic_boom",
      "estimated_duration": 5.0
    }}
  ],
  "call_to_action": "<Kêu gọi bình luận về {topic}>"
}}

Hãy viết kịch bản JSON hoàn chỉnh về "{topic}" ngay bây giờ:"""

async def test():
    res = await llm_client.generate(sys_prompt, user_prompt)
    print("RESULT:")
    print(res)

if __name__ == "__main__":
    asyncio.run(test())


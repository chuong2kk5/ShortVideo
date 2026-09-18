import asyncio
import json
from app.orchestrator.llm_client import llm_client

async def test():
    sys = "You are an AI video script writer. Output only JSON."
    user = """Chủ đề: Thiên nhiên hoang dã kỳ vĩ.
Thời lượng: 30 giây.
BẮT BUỘC tạo đúng 5 phân cảnh (scenes).
Trả về JSON:
{
  "title": "<Tiêu đề>",
  "description": "<Mô tả>",
  "hashtags": ["#shorts"],
  "hook": "<Hook>",
  "scenes": [
    {"scene_index": 0, "narration": "<Lời thoại cảnh 0>", "visual_prompt": "Cinematic shot", "visual_keywords": "nature wildlife", "motion_effect": "zoom_in", "sound_effect_cue": "whoosh", "estimated_duration": 5.0},
    {"scene_index": 1, "narration": "<Lời thoại cảnh 1>", "visual_prompt": "Cinematic shot", "visual_keywords": "nature wildlife", "motion_effect": "pan_left", "sound_effect_cue": "dramatic_boom", "estimated_duration": 5.0},
    {"scene_index": 2, "narration": "<Lời thoại cảnh 2>", "visual_prompt": "Cinematic shot", "visual_keywords": "nature wildlife", "motion_effect": "zoom_out", "sound_effect_cue": "whoosh", "estimated_duration": 5.0},
    {"scene_index": 3, "narration": "<Lời thoại cảnh 3>", "visual_prompt": "Cinematic shot", "visual_keywords": "nature wildlife", "motion_effect": "pan_right", "sound_effect_cue": "heartbeat", "estimated_duration": 5.0},
    {"scene_index": 4, "narration": "<Lời thoại cảnh 4>", "visual_prompt": "Cinematic shot", "visual_keywords": "nature wildlife", "motion_effect": "ken_burns", "sound_effect_cue": "suspense_riser", "estimated_duration": 5.0}
  ],
  "call_to_action": "<CTA>"
}"""
    resp = await llm_client.generate(sys, user)
    clean = resp.strip()
    if clean.startswith("```json"): clean = clean[7:]
    if clean.startswith("```"): clean = clean[3:]
    if clean.endswith("```"): clean = clean[:-3]
    data = json.loads(clean.strip())
    print("Title:", data.get("title"))
    print("Number of scenes generated:", len(data.get("scenes", [])))
    for s in data.get("scenes", []):
        print(f" - Scene {s.get('scene_index')}: {s.get('narration')[:60]}... ({s.get('estimated_duration')}s)")

if __name__ == "__main__":
    asyncio.run(test())


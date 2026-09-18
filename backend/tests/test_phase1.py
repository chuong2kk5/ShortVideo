import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
TEST_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TEST_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Use test sqlite db
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test_app.db"

from app.core.database import init_db, engine, AsyncSessionLocal
from app.core.memory_guard import memory_guard
from app.models.schemas import VideoScriptSchema, SceneSchema
from app.orchestrator.json_repair import json_validator, extract_json_from_text


async def test_database_init():
    print("\n--- 1. Testing Database Table Initialization ---")
    await init_db()
    print("Database tables initialized successfully!")


async def test_memory_guard():
    print("\n--- 2. Testing Memory Guard Metrics & Stage ---")
    health = memory_guard.get_full_health()
    print(f"System RAM: {health['ram']['percent']}% used ({health['ram']['used_mb']} MB)")
    print(f"GPU Info: {health['vram']['gpu_name']}, Available: {health['vram']['available']}")

    async with memory_guard.stage("test_stage"):
        print(f"Inside stage context: active_stage = {memory_guard.current_stage}")
        assert memory_guard.current_stage == "test_stage"
    print(f"Exited stage context: active_stage = {memory_guard.current_stage}")
    assert memory_guard.current_stage is None
    print("Memory Guard stage execution verified!")


def test_self_healing_json():
    print("\n--- 3. Testing Self-Healing JSON Validator ---")
    # Test case 1: Raw JSON wrapped in Markdown codeblock
    markdown_wrapped = """
Here is your requested video script:
```json
{
  "title": "Bí Mật Khủng Khiếp Về Đại Dương #shorts",
  "description": "95% đại dương vẫn là bí ẩn chưa có lời giải.",
  "hashtags": ["#shorts", "#ocean", "#mystery", "#fyp"],
  "hook": "Dưới đáy đại dương có thứ gì đang chuyển động?",
  "scenes": [
    {
      "scene_index": 0,
      "narration": "Con người mới chỉ khám phá chưa đầy 5% diện tích đại dương.",
      "visual_prompt": "Cinematic vertical 9:16 deep underwater shot, abyssal trench, glowing bioluminescent sea creature, mysterious atmospheric blue volumetric lighting, photorealistic 8k.",
      "motion_effect": "zoom_in",
      "sound_effect_cue": "whoosh",
      "estimated_duration": 4.5
    }
  ],
  "call_to_action": "Bình luận bạn có dám lặn xuống đây không!"
}
```
Hope you like it!
"""
    cleaned = extract_json_from_text(markdown_wrapped)
    assert "{" in cleaned and "}" in cleaned
    instance, err = json_validator.parse_and_validate(markdown_wrapped, VideoScriptSchema)
    assert err is None, f"Expected no error, got: {err}"
    assert instance is not None
    assert instance.title == "Bí Mật Khủng Khiếp Về Đại Dương #shorts"
    assert len(instance.scenes) == 1
    assert instance.scenes[0].motion_effect == "zoom_in"
    print("Markdown-wrapped JSON successfully parsed and validated into VideoScriptSchema!")


async def test_project_crud():
    print("\n--- 4. Testing Project & Scene Database Persistence ---")
    from app.models.db_models import Project, Scene
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        # Create Project
        proj = Project(
            title="Bí Mật Đại Dương",
            topic="Những sinh vật kỳ lạ dưới rãnh Mariana",
            target_duration=30,
            language="vi",
            status="draft",
        )
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
        proj_id = proj.id
        print(f"Created project: {proj.title} (ID: {proj_id})")

        # Add Scene
        scene = Scene(
            project_id=proj_id,
            scene_index=0,
            narration_text="Dưới rãnh Mariana sâu hơn 11.000m...",
            visual_prompt="Mariana trench submarine lights shining into dark abyss",
            motion_effect="zoom_in",
            sound_effect_cue="whoosh",
            estimated_duration=4.0,
        )
        session.add(scene)
        await session.commit()

        # Query back
        res = await session.execute(select(Scene).where(Scene.project_id == proj_id))
        scenes = res.scalars().all()
        assert len(scenes) == 1
        assert scenes[0].narration_text.startswith("Dưới rãnh Mariana")
        print(f"Successfully queried {len(scenes)} scenes for project {proj_id}!")


async def test_api_endpoints():
    print("\n--- 5. Testing FastAPI Endpoints via ASGITransport ---")
    from httpx import ASGITransport, AsyncClient
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test root endpoint
        res = await client.get("/")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "online"
        print(f"Root endpoint OK: {data['app']} v{data['version']}")

        # Test health endpoint
        res = await client.get("/api/system/health")
        assert res.status_code == 200
        health_data = res.json()
        assert "ram" in health_data and "vram" in health_data
        print("System Health endpoint OK: RAM & VRAM detected")

        # Test project creation
        proj_payload = {
            "title": "Top 3 Sự Thật Đáng Sợ",
            "topic": "Những bí ẩn không gian",
            "target_duration": 45,
            "language": "vi",
        }
        res = await client.post("/api/projects", json=proj_payload)
        assert res.status_code == 201
        new_proj = res.json()
        assert new_proj["title"] == "Top 3 Sự Thật Đáng Sợ"
        print(f"Project API creation OK: ID {new_proj['id']}")

        # Test listing projects
        res = await client.get("/api/projects")
        assert res.status_code == 200
        projects_list = res.json()
        assert len(projects_list) >= 1
        print(f"Project Listing API OK: retrieved {len(projects_list)} projects")


async def run_all_tests():
    await test_database_init()
    await test_memory_guard()
    test_self_healing_json()
    await test_project_crud()
    await test_api_endpoints()
    print("\n==================================================")
    print(" ALL PHASE 1 VERIFICATION TESTS PASSED SUCCESSFULLY! ")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_all_tests())

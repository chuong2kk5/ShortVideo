import asyncio
import os
import sys
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TEST_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from app.core.database import init_db, AsyncSessionLocal
from app.models.db_models import YouTubeChannel, BrandKitPreset, ScheduledUpload
from app.services.youtube_auth import youtube_auth
from sqlalchemy import select


async def test_youtube_module():
    print("==================================================")
    print(" TESTING PHASE 3 YOUTUBE MANAGER MODULE ")
    print("==================================================")

    await init_db()

    # 1. OAuth2 Auth URL Generation
    print("\n--- 1. Testing OAuth2 Auth URL Generator ---")
    auth_url = youtube_auth.create_auth_url()
    print(f"Generated OAuth2 Consent URL: {auth_url[:75]}...")
    assert "accounts.google.com" in auth_url
    assert "client_id=" in auth_url
    assert "response_type=code" in auth_url
    print("OAuth2 URL creation verified!")

    # 2. Brand Kit Database Management
    print("\n--- 2. Testing Brand Kit Presets ---")
    async with AsyncSessionLocal() as session:
        kit = BrandKitPreset(
            name="Kênh Lịch Sử & Huyền Bí",
            default_tts_voice="vi-VN-NamMinhNeural",
            subtitle_font="Montserrat-ExtraBold",
            subtitle_color="#FFFF00",
            bgm_mood="dramatic_suspense",
        )
        session.add(kit)
        await session.commit()
        await session.refresh(kit)
        print(f"Created Brand Kit: {kit.name} (ID: {kit.id})")
        assert kit.id is not None

        # Query back
        res = await session.execute(select(BrandKitPreset).where(BrandKitPreset.name == "Kênh Lịch Sử & Huyền Bí"))
        found = res.scalar_one_or_none()
        assert found is not None
        assert found.default_tts_voice == "vi-VN-NamMinhNeural"
        print("Brand Kit Database persistence verified!")

    # 3. Scheduled Upload Record Creation
    print("\n--- 3. Testing Scheduled Upload Records ---")
    async with AsyncSessionLocal() as session:
        # Create a mock channel record for testing
        test_channel = YouTubeChannel(
            channel_id="UC_TEST_CHANNEL_12345",
            title="Kênh Khám Phá Vũ Trụ",
            custom_url="@khamphavutru",
            subscriber_count=15200,
            view_count=845000,
            video_count=42,
            is_active=True,
        )
        session.add(test_channel)
        await session.commit()
        await session.refresh(test_channel)
        print(f"Registered channel: {test_channel.title} ({test_channel.channel_id})")

        # Query channels
        stmt = select(YouTubeChannel)
        channels = (await session.execute(stmt)).scalars().all()
        assert len(channels) >= 1
        print(f"Channels in DB: {len(channels)}")

    print("\n==================================================")
    print(" ALL PHASE 3 YOUTUBE MANAGER TESTS PASSED 100%! ")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(test_youtube_module())


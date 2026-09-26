"""
Automated Test Suite for Product Review & TikTok Affiliate Video Maker
Tests:
1. Media Upload Route (/api/upload/media)
2. Reference Video Upload & Analysis (/api/upload/reference-video)
3. Affiliate Copywriting AI (AffiliateScriptGenerator)
4. 1:1 Mapping between user-uploaded product photos and scene structure
5. ASS Subtitle Generator with TikTok Shop Cart Badges
6. Pipeline Endpoint (/api/pipeline/generate-product-review)
"""

import sys
import os
import io
import asyncio
from pathlib import Path
from PIL import Image

if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import settings
from app.models.schemas import ProductReviewRequest, ProductMediaItem
from app.orchestrator.affiliate_script_generator import affiliate_script_generator
from app.services.ffmpeg_editor import ffmpeg_editor


def create_dummy_product_image(output_path: Path, color: tuple, label: str):
    """Generates a simple 1080x1920 test image with color and label."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1080, 1920), color=color)
    img.save(str(output_path), "JPEG", quality=85)
    return output_path


async def test_upload_product_media_api():
    """Verify multipart media upload saves files and returns correct metadata."""
    temp_dir = settings.get_temp_path() / "test_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)

    img1_path = temp_dir / "test_ao_polo_front.jpg"
    img2_path = temp_dir / "test_ao_polo_fabric.jpg"
    create_dummy_product_image(img1_path, (40, 70, 120), "Front")
    create_dummy_product_image(img2_path, (150, 40, 50), "Fabric")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        with open(img1_path, "rb") as f1, open(img2_path, "rb") as f2:
            files = [
                ("files", ("ao_polo_front.jpg", f1, "image/jpeg")),
                ("files", ("ao_polo_fabric.jpg", f2, "image/jpeg")),
            ]
            response = await ac.post("/api/upload/media", files=files)

        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        assert len(data) == 2
        assert "ao_polo_front" in data[0]["filename"]
        assert data[0]["url"].startswith("/static/uploads/")
        assert os.path.exists(data[0]["local_path"])
        assert data[0]["media_type"] == "image"
        print(f"\n[OK] Uploaded media API test passed: {len(data)} items stored.")


async def test_affiliate_script_generator_mapping():
    """Verify that AffiliateScriptGenerator correctly aligns scenes 1:1 with uploaded photos."""
    media_items = [
        ProductMediaItem(
            url="/static/uploads/front.jpg",
            local_path="d:/test/front.jpg",
            filename="front.jpg",
            media_type="image",
            caption="Ảnh toàn thân áo polo nam",
        ),
        ProductMediaItem(
            url="/static/uploads/fabric.jpg",
            local_path="d:/test/fabric.jpg",
            filename="fabric.jpg",
            media_type="image",
            caption="Cận cảnh chất vải cá sấu cotton 100%",
        ),
        ProductMediaItem(
            url="/static/uploads/fit.jpg",
            local_path="d:/test/fit.jpg",
            filename="fit.jpg",
            media_type="image",
            caption="Lên form người mặc tôn dáng",
        ),
        ProductMediaItem(
            url="/static/uploads/colors.jpg",
            local_path="d:/test/colors.jpg",
            filename="colors.jpg",
            media_type="image",
            caption="Bảng 5 màu sắc trẻ trung",
        ),
    ]

    req = ProductReviewRequest(
        product_name="Áo Polo Nam Cotton Cổ Dệt",
        category="fashion",
        key_features="Chất vải cá sấu dệt tổ ong thoáng khí, co giãn 4 chiều không xù lông",
        deal_info="Giảm giá sốc 99k tặng voucher freeship trong giỏ hàng góc trái",
        template_type="fashion_ootd",
        media_items=media_items,
        voice="vi-VN-HoaiMyNeural",
        target_duration=30,
        language="vi",
    )

    script = await affiliate_script_generator.generate_review_script(req)

    assert script.title is not None
    assert len(script.scenes) == len(media_items), (
        f"Expected {len(media_items)} scenes to match uploaded photos, got {len(script.scenes)}"
    )

    # Check that motion effects include product motion
    motion_effects = [s.motion_effect for s in script.scenes]
    assert any(m in ["macro_zoom", "showcase_pan", "zoom_in", "pan_right"] for m in motion_effects)

    # Check that CTA emphasizes cart
    assert any(
        w in script.call_to_action.lower() for w in ["giỏ hàng", "mua", "deal", "săn", "ưu đãi", "bấm"]
    )
    print(f"\n[OK] Affiliate script generated with {len(script.scenes)} scenes matching {len(media_items)} photos.")
    print(f"     Title: {script.title}")
    print(f"     Hook: {script.hook}")
    print(f"     CTA: {script.call_to_action}")


def test_ass_subtitle_affiliate_badges():
    """Verify that ASS subtitles generate TikTok Shop cart badge for affiliate mode."""
    test_ass_path = settings.get_temp_path() / "test_affiliate_sub.ass"
    dummy_cues = [
        {"word": "SĂN", "start": 0.5, "end": 0.9},
        {"word": "DEAL", "start": 0.9, "end": 1.3},
        {"word": "ÁO", "start": 1.3, "end": 1.7},
        {"word": "POLO", "start": 1.7, "end": 2.2},
    ]

    ffmpeg_editor.generate_ass_subtitle_file(
        scene_word_cues=dummy_cues,
        output_ass_path=test_ass_path,
        title="Áo Polo Nam Siêu Hot",
        call_to_action="Bấm giỏ hàng góc trái săn deal 99k ngay!",
        total_duration=15.0,
        is_affiliate=True,
    )

    assert test_ass_path.exists()
    content = test_ass_path.read_text(encoding="utf-8")

    assert "TikTokCartBadge" in content
    assert "GIỎ HÀNG CHÍNH HÃNG" in content
    assert "🛒" in content
    print("\n[OK] ASS subtitle file generated with TikTok Shop Cart badge styling.")


async def test_generate_product_review_endpoint():
    """Verify POST /api/pipeline/generate-product-review creates project and job."""
    temp_dir = settings.get_temp_path() / "test_e2e_prod"
    temp_dir.mkdir(parents=True, exist_ok=True)
    img_path = temp_dir / "sample_watch.jpg"
    create_dummy_product_image(img_path, (20, 20, 20), "Watch")

    payload = {
        "product_name": "Đồng Hồ Nam Dây Da Cao Cấp",
        "category": "accessories",
        "key_features": "Kính khoáng chống xước, chống nước 3ATM, dây da thật 100%",
        "deal_info": "Ưu đãi khai trương giảm 60%, bảo hành 12 tháng",
        "target_audience": "Nam giới văn phòng",
        "template_type": "accessories_unboxing",
        "media_items": [
            {
                "url": "/static/uploads/sample_watch.jpg",
                "local_path": str(img_path.resolve()),
                "filename": "sample_watch.jpg",
                "media_type": "image",
                "caption": "Mặt đồng hồ và dây da thật",
            }
        ],
        "voice": "vi-VN-NamMinhNeural",
        "target_duration": 20,
        "language": "vi",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/pipeline/generate-product-review", json=payload)
        assert response.status_code == 200, f"Endpoint failed: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert "project_id" in data
        assert "job_id" in data
        assert data["scenes_count"] >= 1
        print(f"\n[OK] POST /api/pipeline/generate-product-review succeeded! Job ID: {data['job_id']}")


if __name__ == "__main__":
    print("Running Product Review & Affiliate tests directly...")
    asyncio.run(test_upload_product_media_api())
    test_ass_subtitle_affiliate_badges()
    asyncio.run(test_affiliate_script_generator_mapping())
    asyncio.run(test_generate_product_review_endpoint())
    print("\nALL PRODUCT REVIEW TESTS PASSED SUCCESSFULLY! 🎉")

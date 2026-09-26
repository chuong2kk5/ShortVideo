import json
import logging
import re
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.memory_guard import memory_guard
from app.models.db_models import Project, Scene
from app.models.schemas import (
    VideoScriptSchema,
    SceneSchema,
    ProductReviewRequest,
    ProductMediaItem,
)
from app.orchestrator.llm_client import llm_client
from app.orchestrator.json_repair import json_validator

logger = logging.getLogger("affiliate_script_generator")

AFFILIATE_SYSTEM_PROMPT = """Bạn là Chuyên Gia Sáng Tạo Nội Dung TikTok Shop & KOC Review Hàng Đầu (Top 1% Creator).
Nhiệm vụ của bạn là viết kịch bản review sản phẩm ĐÍNH KÈM GIỎ HÀNG TIKTOK SHOP đạt tỷ lệ chuyển đổi đơn hàng (CR) cao nhất.

CÁC NGUYÊN TẮC BẮT BUỘC:
1. PHONG CÁCH NÓI:
   - Giọng điệu chân thực, gần gũi như một người bạn thân đang chia sẻ món đồ xịn sò vừa tậu được.
   - Sử dụng ngôn từ viral TikTok Việt Nam tự nhiên: "mê chữ ê kéo dài", "chất lừ", "form chuẩn đét", "ưng bụng", "hạt dẻ", "săn deal hời".
   - Tuyệt đối KHÔNG viết văn miêu tả khô khan, sáo rỗng kiểu văn xuôi trường lớp.

2. CẤU TRÚC CHUYỂN ĐỔI CAO:
   - 0-3s đầu (HOOK): Đập tan do dự, đánh vào nỗi đau hoặc sự bất ngờ ("Ai bảo dưới 100 cành không mua được áo polo form xịn?").
   - Giữa video (BODY): Từng câu thoại phải khớp chính xác với hình ảnh sản phẩm đang hiển thị (chất vải, đường may, form dáng, trải nghiệm thực tế).
   - 3s cuối (CALL TO ACTION): Kêu gọi bấm ngay vào GIỎ HÀNG GÓC TRÁI bên dưới để nhận voucher/flash sale.

3. KHỚP CHÍNH XÁC VỚI SỐ ẢNH NGƯỜI DÙNG CUNG CẤP:
   - Kịch bản PHẢI CÓ ĐÚNG số lượng phân cảnh (scenes) tương ứng với danh sách ảnh/media người dùng đã tải lên.
   - Mỗi phân cảnh phải chọn hiệu ứng camera phù hợp:
     * Cận cảnh chất liệu/chi tiết: "macro_zoom"
     * Lên dáng/toàn thân trang phục: "showcase_pan"
     * Giới thiệu mở đầu: "zoom_in"
     * Bảng màu hoặc góc khác: "pan_right" hoặc "pan_left"
     * Kêu gọi mua: "zoom_out"

4. ĐỊNH DẠNG JSON ĐẦU RA BẮT BUỘC:
{
  "title": "Tiêu đề video review giật tít, kích thích bấm vào",
  "description": "Mô tả chuẩn SEO TikTok Shop kèm hashtag",
  "hashtags": ["#tiktokshop", "#reviewthoitrang", "#ootd", "#dealhot"],
  "hook": "Câu mở đầu 0-3s cuốn hút",
  "call_to_action": "Bấm ngay giỏ hàng góc trái để săn deal giảm giá và freeship nhé!",
  "scenes": [
    {
      "scene_index": 0,
      "narration": "Lời thoại ngắn gọn, xúc tích cho ảnh 1",
      "visual_prompt": "English prompt describing the product scene",
      "visual_keywords": "product fashion review",
      "motion_effect": "zoom_in",
      "sound_effect_cue": "whoosh",
      "estimated_duration": 4.0
    }
  ]
}
"""


class AffiliateScriptGenerator:
    """
    Generates high-converting TikTok Shop / Affiliate review scripts
    and maps them 1:1 to user-uploaded product photos/videos.
    """

    def _build_product_prompt(self, request: ProductReviewRequest) -> str:
        media_count = max(len(request.media_items), 1)
        media_descriptions = []
        for i, item in enumerate(request.media_items):
            cap = item.caption or f"Ảnh chi tiết sản phẩm {i+1}"
            media_descriptions.append(f"  - Phân cảnh {i+1} (Ảnh {i+1}): {cap} [Loại: {item.media_type}]")

        media_list_str = "\n".join(media_descriptions) if media_descriptions else "  - Cảnh tổng quan sản phẩm"

        template_guidance = {
            "fashion_ootd": "Cấu trúc Thời Trang OOTD: Hook bất ngờ về giá/form -> Cận cảnh chất vải & co giãn -> Lên form người mặc -> Bảng màu/phối đồ -> Kêu gọi giỏ hàng.",
            "accessories_unboxing": "Cấu trúc Phụ Kiện/Giày/Túi: Hook độ sang xịn -> Cận cảnh chi tiết khuy khóa/đường may -> Phối cùng trang phục -> Deal hời giỏ hàng.",
            "gadget_practical": "Cấu trúc Đồ Tiện Ích/Gia Dụng: Nỗi đau đời thường -> Giải pháp tiện lợi -> Test công năng thực tế -> Giá sốc giỏ hàng.",
            "beauty_review": "Cấu trúc Mỹ Phẩm/Chăm Sóc: Vấn đề về da -> Test chất kem/texture mềm mịn -> Cảm giác sau khi dùng -> Ưu đãi giỏ hàng.",
            "reference_match": "Bắt chước nhịp điệu video mẫu: Tiết tấu dồn dập, giật tít mạnh, chuyển cảnh nhanh, chốt sale gấp rút.",
        }.get(request.template_type, "KOC Review thực tế, tập trung ưu điểm nổi bật và deal hot.")

        prompt = f"""Hãy viết kịch bản TikTok Shop Review cho sản phẩm sau:

THÔNG TIN SẢN PHẨM:
- Tên sản phẩm: {request.product_name}
- Ngành hàng: {request.category}
- Đặc điểm / Chất liệu nổi bật: {request.key_features}
- Giá / Khuyến mãi hấp dẫn: {request.deal_info or 'Đang flash sale giảm sâu trong giỏ hàng'}
- Đối tượng khách hàng: {request.target_audience or 'Mọi người'}
- Định hướng phong cách: {template_guidance}

DANH SÁCH ẢNH/MEDIA THẬT NGƯỜI DÙNG ĐÃ TẢI LÊN ({media_count} ảnh):
{media_list_str}

YÊU CẦU ĐẶC BIỆT QUAN TRỌNG:
1. Bạn PHẢI tạo CHÍNH XÁC {media_count} phân cảnh trong mảng `scenes` (tương ứng từ ảnh 1 đến ảnh {media_count}).
2. Lời thoại của từng cảnh phải bám sát nội dung của bức ảnh tương ứng.
3. Thời lượng mỗi cảnh từ 3.0 đến 4.5 giây để video có nhịp điệu lướt nhanh, cuốn hút.
4. Cảnh cuối cùng PHẢI là lời kêu gọi bấm vào GIỎ HÀNG GÓC TRÁI nhận ưu đãi.
5. Chỉ trả về duy nhất khối JSON hợp lệ theo đúng cấu trúc đã chỉ định.
"""
        return prompt

    async def generate_review_script(self, request: ProductReviewRequest) -> VideoScriptSchema:
        user_prompt = self._build_product_prompt(request)
        target_scene_count = max(len(request.media_items), 3)

        logger.info(
            f"Generating Affiliate review script for '{request.product_name}' "
            f"({len(request.media_items)} media items, category={request.category})..."
        )

        async with memory_guard.stage("script_generation"):
            raw_response = await llm_client.generate(
                system_prompt=AFFILIATE_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.7,
            )

            validated: VideoScriptSchema = await json_validator.execute_with_self_healing(
                initial_raw_text=raw_response,
                schema_cls=VideoScriptSchema,
                llm_generate_fn=llm_client.generate,
                system_prompt=AFFILIATE_SYSTEM_PROMPT,
            )

            # Ensure scenes count matches media_items count if media_items provided
            validated = self._align_scenes_with_media(validated, request.media_items)

        logger.info(
            f"Affiliate review script generated: '{validated.title}' with {len(validated.scenes)} scenes."
        )
        return validated

    def _align_scenes_with_media(
        self, script: VideoScriptSchema, media_items: List[ProductMediaItem]
    ) -> VideoScriptSchema:
        """
        Guarantees that script.scenes has exactly the same length as media_items (if media_items >= 2).
        If LLM created fewer or more, neatly aligns them so each photo has its own scene.
        """
        if not media_items:
            return script

        req_count = len(media_items)
        curr_count = len(script.scenes)

        if curr_count == req_count:
            return script

        scenes = list(script.scenes)

        if curr_count > req_count:
            # Trim excess scenes, but ensure outro CTA is preserved on the last scene
            last_scene = scenes[-1]
            scenes = scenes[:req_count]
            if req_count > 0:
                scenes[-1].narration = last_scene.narration
                scenes[-1].motion_effect = "zoom_out"
        else:
            # Need more scenes: Duplicate or expand from existing scenes
            while len(scenes) < req_count:
                idx = len(scenes)
                motion = "macro_zoom" if idx % 2 == 1 else "showcase_pan"
                scenes.append(
                    SceneSchema(
                        scene_index=idx,
                        narration=f"Chi tiết sản phẩm tiếp theo cực kỳ tinh tế, xem ngay trong giỏ hàng!",
                        visual_prompt=f"Detailed view of product {idx+1}",
                        visual_keywords="product details",
                        motion_effect=motion,
                        sound_effect_cue="whoosh",
                        estimated_duration=3.5,
                    )
                )

        # Re-index scenes
        for i, sc in enumerate(scenes):
            sc.scene_index = i

        script.scenes = scenes
        return script

    async def save_affiliate_script_to_project(
        self,
        db: AsyncSession,
        project_id: str,
        script: VideoScriptSchema,
        media_items: List[ProductMediaItem],
    ) -> Project:
        """
        Saves the affiliate script to the database and binds the real uploaded product photos
        directly to Scene.image_path so that Stage 2 skips AI image generation!
        """
        res = await db.execute(select(Project).where(Project.id == project_id))
        project = res.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        project.title = script.title
        project.seo_title = script.title
        project.seo_description = script.description
        project.hashtags = script.hashtags
        project.status = "ready_to_render"

        # Clear existing scenes
        await db.execute(delete(Scene).where(Scene.project_id == project_id))

        # Assign uploaded photos 1:1 to scenes
        for idx, scene_data in enumerate(script.scenes):
            assigned_image_path = None
            assigned_status = "pending"

            if idx < len(media_items):
                assigned_image_path = media_items[idx].local_path
                assigned_status = "image_ready"
            elif len(media_items) > 0:
                # Fallback to cycling media items if scenes exceed media
                fallback_item = media_items[idx % len(media_items)]
                assigned_image_path = fallback_item.local_path
                assigned_status = "image_ready"

            scene = Scene(
                project_id=project_id,
                scene_index=scene_data.scene_index,
                narration_text=scene_data.narration,
                visual_prompt=scene_data.visual_prompt,
                visual_keywords=getattr(scene_data, "visual_keywords", "product review"),
                motion_effect=scene_data.motion_effect,
                sound_effect_cue=scene_data.sound_effect_cue,
                estimated_duration=scene_data.estimated_duration,
                image_path=assigned_image_path,
                status=assigned_status,
            )
            db.add(scene)

        await db.commit()
        await db.refresh(project)
        return project


affiliate_script_generator = AffiliateScriptGenerator()

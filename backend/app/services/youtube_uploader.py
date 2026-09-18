import asyncio
import datetime
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from googleapiclient.http import MediaFileUpload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.db_models import YouTubeChannel, ScheduledUpload, Project
from app.services.youtube_auth import youtube_auth

logger = logging.getLogger("youtube_uploader")


class YouTubeUploader:
    """
    YouTube Shorts Auto Publisher & Scheduler:
    - Uploads MP4 videos to YouTube Shorts via YouTube Data API v3 (Resumable).
    - Injects SEO metadata (viral Title with #Shorts, Description, Tags).
    - Supports immediate publishing (public) or future scheduled release.
    """

    async def upload_video(
        self,
        db: AsyncSession,
        channel_id: str,
        video_path: Path,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        privacy_status: str = "private",
        scheduled_publish_time: Optional[datetime.datetime] = None,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Uploads video to YouTube Shorts.
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Fetch channel from DB
        stmt = select(YouTubeChannel).where(YouTubeChannel.id == channel_id)
        res = await db.execute(stmt)
        channel = res.scalar_one_or_none()
        if not channel or not channel.credentials_json:
            raise ValueError(f"Channel {channel_id} not found or has no active credentials.")

        # Ensure #Shorts is present in title
        clean_title = title.strip()
        if "#shorts" not in clean_title.lower():
            clean_title = f"{clean_title[:85]} #Shorts"

        tag_list = tags or ["#Shorts", "Shorts", "TikTok", "Viral"]

        body: Dict[str, Any] = {
            "snippet": {
                "title": clean_title[:100],
                "description": description,
                "tags": tag_list,
                "categoryId": "22",  # People & Blogs
            },
            "status": {
                "privacyStatus": privacy_status if not scheduled_publish_time else "private",
                "selfDeclaredMadeForKids": False,
            },
        }

        # Handle scheduled publish time
        if scheduled_publish_time:
            # YouTube requires RFC 3339 formatted date
            body["status"]["publishAt"] = scheduled_publish_time.astimezone(datetime.timezone.utc).isoformat()
            body["status"]["privacyStatus"] = "private"

        logger.info(f"Initiating YouTube Shorts upload for '{clean_title}' to channel '{channel.title}'...")

        # Build authenticated service
        service = youtube_auth.get_service_from_credentials(channel.credentials_json)

        # Upload using MediaFileUpload
        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            chunksize=1024 * 1024 * 4,  # 4MB chunks
            resumable=True,
        )

        request = service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        # Execute upload in threadpool since googleapiclient is synchronous
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, request.execute)

        video_id = response.get("id")
        shorts_url = f"https://www.youtube.com/shorts/{video_id}"
        logger.info(f"YouTube Shorts upload SUCCESS: {shorts_url}")

        # Create or update ScheduledUpload record
        if project_id:
            upload_record = ScheduledUpload(
                channel_id=channel.id,
                project_id=project_id,
                title=clean_title,
                description=description,
                tags=",".join(tag_list),
                privacy_status=privacy_status,
                scheduled_publish_time=scheduled_publish_time,
                status="published" if not scheduled_publish_time else "scheduled",
                youtube_video_id=video_id,
                uploaded_at=datetime.datetime.now(datetime.timezone.utc),
            )
            db.add(upload_record)
            await db.commit()

        return {
            "video_id": video_id,
            "shorts_url": shorts_url,
            "title": clean_title,
            "status": body["status"]["privacyStatus"],
            "scheduled_at": body["status"].get("publishAt"),
        }


youtube_uploader = YouTubeUploader()


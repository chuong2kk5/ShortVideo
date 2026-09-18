import asyncio
import datetime
import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.db_models import YouTubeChannel
from app.services.youtube_auth import youtube_auth

logger = logging.getLogger("youtube_analytics")


class YouTubeAnalyticsFetcher:
    """
    Channel Analytics Fetcher:
    - Queries YouTube Data API v3 for latest channel views, likes, comments, and subscribers.
    - Synchronizes statistics into the local database for Dashboard display.
    """

    async def sync_channel_analytics(self, db: AsyncSession, channel_db_id: str) -> Dict[str, Any]:
        """Fetch latest statistics for a specific channel and updates local DB."""
        stmt = select(YouTubeChannel).where(YouTubeChannel.id == channel_db_id)
        res = await db.execute(stmt)
        channel = res.scalar_one_or_none()
        if not channel or not channel.credentials_json:
            raise ValueError("Channel not found or missing credentials.")

        service = youtube_auth.get_service_from_credentials(channel.credentials_json)

        loop = asyncio.get_event_loop()

        # 1. Fetch channel stats
        def _get_ch_stats():
            return (
                service.channels()
                .list(id=channel.channel_id, part="snippet,statistics")
                .execute()
            )

        ch_response = await loop.run_in_executor(None, _get_ch_stats)
        items = ch_response.get("items", [])
        if not items:
            raise ValueError("YouTube API returned no data for this channel.")

        stats = items[0].get("statistics", {})
        channel.subscriber_count = int(stats.get("subscriberCount", 0))
        channel.view_count = int(stats.get("viewCount", 0))
        channel.video_count = int(stats.get("videoCount", 0))
        channel.last_synced_at = datetime.datetime.now(datetime.timezone.utc)

        # 2. Fetch recent videos (up to 10 videos)
        def _get_recent_videos():
            search_res = (
                service.search()
                .list(
                    channelId=channel.channel_id,
                    part="id,snippet",
                    order="date",
                    maxResults=10,
                    type="video",
                )
                .execute()
            )
            v_ids = [item["id"]["videoId"] for item in search_res.get("items", [])]
            if not v_ids:
                return []

            # Fetch detailed metrics for these videos
            videos_res = (
                service.videos()
                .list(id=",".join(v_ids), part="snippet,statistics")
                .execute()
            )
            video_list = []
            for v in videos_res.get("items", []):
                v_stats = v.get("statistics", {})
                video_list.append(
                    {
                        "video_id": v["id"],
                        "title": v.get("snippet", {}).get("title"),
                        "published_at": v.get("snippet", {}).get("publishedAt"),
                        "views": int(v_stats.get("viewCount", 0)),
                        "likes": int(v_stats.get("likeCount", 0)),
                        "comments": int(v_stats.get("commentCount", 0)),
                        "url": f"https://www.youtube.com/shorts/{v['id']}",
                    }
                )
            return video_list

        recent_videos = await loop.run_in_executor(None, _get_recent_videos)

        await db.commit()
        await db.refresh(channel)

        return {
            "channel_id": channel.channel_id,
            "title": channel.title,
            "subscribers": channel.subscriber_count,
            "total_views": channel.view_count,
            "total_videos": channel.video_count,
            "last_synced_at": channel.last_synced_at.isoformat(),
            "recent_videos": recent_videos,
        }


youtube_analytics = YouTubeAnalyticsFetcher()


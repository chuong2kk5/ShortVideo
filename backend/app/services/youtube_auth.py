import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build, Resource
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings, BASE_DIR
from app.models.db_models import YouTubeChannel

logger = logging.getLogger("youtube_auth")

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


class YouTubeAuthManager:
    """
    Multi-Channel YouTube OAuth2 Manager:
    - Generates Google OAuth2 consent URL.
    - Exchanges auth code for credentials (access_token, refresh_token).
    - Automatically refreshes expired tokens.
    - Builds authenticated YouTube Data API v3 client.
    """

    def _get_client_secrets_path(self) -> Path:
        p = settings.resolve_path(settings.YOUTUBE_CLIENT_SECRETS_FILE)
        if not p.exists():
            # Create a sample client_secrets.json if not present
            p.parent.mkdir(parents=True, exist_ok=True)
            sample_secrets = {
                "installed": {
                    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
                    "project_id": "ai-shorts-factory",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": "YOUR_CLIENT_SECRET",
                    "redirect_uris": ["http://localhost:8000/api/youtube/oauth2callback"],
                }
            }
            p.write_text(json.dumps(sample_secrets, indent=2), encoding="utf-8")
        return p

    def create_auth_url(self, redirect_uri: str = "http://localhost:8000/api/youtube/oauth2callback") -> str:
        """Generates Google OAuth2 authorization URL."""
        secrets_path = self._get_client_secrets_path()
        flow = Flow.from_client_secrets_file(
            str(secrets_path),
            scopes=YOUTUBE_SCOPES,
            redirect_uri=redirect_uri,
        )
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return auth_url

    async def handle_oauth_callback(
        self,
        code: str,
        redirect_uri: str,
        db: AsyncSession,
    ) -> YouTubeChannel:
        """
        Exchanges authorization code for tokens, retrieves channel info from YouTube,
        and saves/updates channel in SQLite.
        """
        secrets_path = self._get_client_secrets_path()
        flow = Flow.from_client_secrets_file(
            str(secrets_path),
            scopes=YOUTUBE_SCOPES,
            redirect_uri=redirect_uri,
        )
        flow.fetch_token(code=code)
        creds = flow.credentials

        # Fetch channel metadata
        youtube = build("youtube", "v3", credentials=creds)
        res = youtube.channels().list(mine=True, part="snippet,statistics").execute()
        items = res.get("items", [])
        if not items:
            raise ValueError("No YouTube channel associated with this Google account.")

        ch_data = items[0]
        channel_id = ch_data["id"]
        snippet = ch_data.get("snippet", {})
        stats = ch_data.get("statistics", {})

        creds_json = creds.to_json()

        # Check existing channel in database
        stmt = select(YouTubeChannel).where(YouTubeChannel.channel_id == channel_id)
        existing = (await db.execute(stmt)).scalar_one_or_none()

        if existing:
            channel = existing
            channel.title = snippet.get("title", channel.title)
            channel.custom_url = snippet.get("customUrl")
            channel.thumbnail_url = snippet.get("thumbnails", {}).get("default", {}).get("url")
            channel.credentials_json = creds_json
            channel.subscriber_count = int(stats.get("subscriberCount", 0))
            channel.view_count = int(stats.get("viewCount", 0))
            channel.video_count = int(stats.get("videoCount", 0))
            channel.is_active = True
        else:
            channel = YouTubeChannel(
                channel_id=channel_id,
                title=snippet.get("title", "YouTube Channel"),
                custom_url=snippet.get("customUrl"),
                thumbnail_url=snippet.get("thumbnails", {}).get("default", {}).get("url"),
                credentials_json=creds_json,
                subscriber_count=int(stats.get("subscriberCount", 0)),
                view_count=int(stats.get("viewCount", 0)),
                video_count=int(stats.get("videoCount", 0)),
                is_active=True,
            )
            db.add(channel)

        await db.commit()
        await db.refresh(channel)
        logger.info(f"Connected YouTube channel: {channel.title} ({channel.channel_id})")
        return channel

    def get_service_from_credentials(self, credentials_json_str: str) -> Resource:
        """Constructs an authorized YouTube Resource from saved credentials JSON."""
        creds_dict = json.loads(credentials_json_str)
        creds = Credentials.from_authorized_user_info(creds_dict, scopes=YOUTUBE_SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return build("youtube", "v3", credentials=creds)


youtube_auth = YouTubeAuthManager()


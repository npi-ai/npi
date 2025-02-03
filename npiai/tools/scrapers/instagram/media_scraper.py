import re
import asyncio
from typing import List
from instagrapi import Client as InstagramClient
from instagrapi.types import Media, HttpUrl

from npiai import Context
from npiai.tools.scrapers import BaseScraper, SourceItem


class InstagramMediaScraper(BaseScraper):
    name = "instagram_media_scraper"
    description = "Scrape posts from an Instagram account"
    system_prompt = "You are an Instagram media scraper tasked with extracting posts from the given account."

    _client: InstagramClient
    _user_id: str
    _pagination_code: str | None
    _load_media_lock: asyncio.Lock

    def __init__(
        self,
        client: InstagramClient,
        username_or_url: str,
    ):
        super().__init__()
        self._client = client
        self._pagination_code = None
        self._load_media_lock = asyncio.Lock()

        # check if the input is a URL
        url_pattern = re.compile(r"(?:https://)?www.instagram.com/([^/]+)/?")

        match = url_pattern.match(username_or_url)
        username = match.group(1) if match else username_or_url

        # user_id_from_username() will raise JSONDecodeError
        # see: https://github.com/subzeroid/instagrapi/issues/1802#issuecomment-1944589499
        self._user_id = client.user_info_by_username_v1(username).pk

    async def init_data(self, ctx: Context):
        self._pagination_code = None

    async def next_items(self, ctx: Context, count: int) -> List[SourceItem] | None:
        async with self._load_media_lock:
            all_media, pagination_code = self._client.user_medias_paginated(
                user_id=self._user_id,
                amount=count,
                end_cursor=self._pagination_code,
            )

            if not all_media:
                return None

            self._pagination_code = pagination_code

            return [self._parse_media(media) for media in all_media]

    def _parse_media(self, media: Media) -> SourceItem:
        res = {
            "url": f"https://www.instagram.com/p/{media.code}/",
            "caption": media.caption_text or media.accessibility_caption,
            "timestamp": media.taken_at.isoformat(),
            "media_type": self._get_media_type(media),
            "comments": media.comment_count,
            "likes": media.like_count,
            "thumbnail": self._parse_url(media.thumbnail_url),
        }

        if media.video_url:
            res["video"] = self._parse_url(media.video_url)

        if media.resources:
            resources = []

            for r in media.resources:
                resources.append(
                    {
                        "thumbnail": self._parse_url(r.thumbnail_url),
                        "video": self._parse_url(r.video_url),
                    }
                )

            res["resources"] = resources

        return SourceItem(
            hash=media.id,
            data=res,
        )

    def _get_media_type(self, media: Media) -> str | None:
        if media.media_type == 1:
            return "photo"

        if media.media_type == 2:
            if media.product_type == "feed":
                return "video"
            return media.product_type

        if media.media_type == 8:
            return "album"

    def _parse_url(self, url: HttpUrl) -> str:
        return url.unicode_string() if url else None

from typing import List
from instagrapi import Client as InstagramClient
from instagrapi.types import Comment

from npiai import Context
from npiai.tools.scrapers import BaseScraper, SourceItem


class InstagramCommentsScraper(BaseScraper):
    name = "instagram_comments_scraper"
    description = "Scrape comments from an Instagram post"
    system_prompt = "You are an Instagram comments scraper tasked with extracting comments from the given post."

    _client: InstagramClient
    _media_id: str
    _pagination_code: str | None

    _remaining_comments: List[Comment]

    def __init__(
        self,
        client: InstagramClient,
        url: str,
    ):
        super().__init__()
        self._client = client
        self._pagination_code = None
        self._remaining_comments = []

        media_pk = client.media_pk_from_url(url)
        self._media_id = client.media_id(media_pk)

    async def next_items(self, ctx: Context, count: int) -> List[SourceItem] | None:
        all_comments = self._fetch_more_comments(count)

        res: List[SourceItem] = []

        for comment in all_comments:
            res.append(
                SourceItem(
                    hash=comment.pk,
                    data={
                        "username": comment.user.username,
                        "text": comment.text,
                        "timestamp": comment.created_at_utc.isoformat(),
                        "likes": comment.like_count,
                    },
                )
            )

        return res

    def _fetch_more_comments(self, count: int):
        if len(self._remaining_comments) < count:
            all_comments, pagination_code = self._client.media_comments_chunk(
                media_id=self._media_id,
                max_amount=count,
                min_id=self._pagination_code,
            )

            self._pagination_code = pagination_code

            if all_comments:
                self._remaining_comments.extend(all_comments)

        res = self._remaining_comments[:count]
        self._remaining_comments = self._remaining_comments[count:]
        return res

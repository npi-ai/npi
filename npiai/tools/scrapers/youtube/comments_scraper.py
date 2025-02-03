from typing import Generator, List

from youtube_comment_downloader import YoutubeCommentDownloader

from npiai import Context
from npiai.tools.scrapers import BaseScraper, SourceItem


class YouTubeCommentsScraper(BaseScraper):
    name = "youtube_comments_scraper"
    description = "Scrape comments from a YouTube video"
    system_prompt = "You are a YouTube comments scraper tasked with extracting comments from the given video."

    _url: str
    _downloader: YoutubeCommentDownloader
    _comments_generator: Generator[dict, None, None]

    def __init__(self, url: str):
        super().__init__()
        self._url = url
        self._downloader = YoutubeCommentDownloader()

    async def init_data(self, ctx: Context):
        self._comments_generator = self._downloader.get_comments_from_url(
            youtube_url=self._url,
            language="en",
        )

    async def next_items(self, ctx: Context, count: int) -> List[SourceItem] | None:
        items = []

        for _ in range(count):
            try:
                comment = next(self._comments_generator)
            except StopIteration:
                break
            items.append(
                SourceItem(
                    hash=comment["cid"],
                    data=comment,
                )
            )

        return items

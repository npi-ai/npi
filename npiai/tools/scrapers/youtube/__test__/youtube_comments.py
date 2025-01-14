import asyncio
import json
import time

from npiai.tools.scrapers.youtube import YouTubeCommentsScraper

from npiai.utils.test_utils import DebugContext


async def main():
    ctx = DebugContext()
    async with YouTubeCommentsScraper(
        url="https://www.youtube.com/watch?v=CD8mr0zrLj0"
    ) as scraper:
        step_start_time = time.monotonic()
        columns = await scraper.infer_columns(
            ctx=ctx,
        )

        print(
            f"({time.monotonic() - step_start_time:.2f}s) Inferred columns:",
            json.dumps(columns, indent=2),
        )

        start = time.monotonic()
        count = 0

        async for items in scraper.summarize_stream(
            ctx=ctx,
            output_columns=columns,
            limit=100,
            batch_size=5,
            concurrency=10,
        ):
            print("Chunk:", json.dumps(items, indent=2, ensure_ascii=False))
            count += len(items["items"])

        end = time.monotonic()
        print(f"Summarized {count} items in {end - start:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())

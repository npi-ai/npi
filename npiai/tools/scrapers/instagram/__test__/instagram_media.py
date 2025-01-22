import os
import asyncio
import json
import time

from instagrapi import Client as InstagramClient

from npiai.tools.scrapers.instagram import InstagramMediaScraper
from npiai.llm import OpenAI

from npiai.utils.test_utils import DebugContext


async def main():
    ctx = DebugContext()
    ctx.use_llm(OpenAI(api_key=os.environ["OPENAI_API_KEY"], model="gpt-4o-mini"))
    client = InstagramClient()
    client.login_by_sessionid(os.environ["INSTAGRAM_SESSIONID"])

    async with InstagramMediaScraper(
        client=client,
        username_or_url="https://www.instagram.com/lilasikuta/",
    ) as scraper:
        step_start_time = time.monotonic()
        columns = await scraper.infer_columns(
            ctx=ctx,
            sample_size=10,
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

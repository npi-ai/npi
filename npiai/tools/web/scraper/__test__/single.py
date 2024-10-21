import asyncio
import json

from npiai.tools.web.scraper import Scraper
from npiai.utils.test_utils import DebugContext


async def main():
    async with Scraper(headless=False, batch_size=10) as scraper:
        columns = await scraper.infer_columns(
            ctx=DebugContext(),
            url="https://www.bardeen.ai/playbooks/get-data-from-the-currently-opened-imdb-com-title-page",
        )
        print("Inferred columns:", json.dumps(columns, indent=2))

        stream = scraper.summarize_stream(
            ctx=DebugContext(),
            url="https://www.bardeen.ai/playbooks/get-data-from-the-currently-opened-imdb-com-title-page",
            limit=1,
            output_columns=columns,
        )

        async for items in stream:
            print("Chunk:", json.dumps(items, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

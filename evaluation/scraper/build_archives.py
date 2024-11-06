import pathlib

from npiai.utils.test_utils import DebugContext
from npiai.tools.web.scraper import Scraper

from configs import configs

ARCHIVE_DIR = pathlib.Path(__file__).parent / "archives"


async def archive_bardeen():
    async with Scraper(headless=False, batch_size=10) as scraper:
        har_file = ARCHIVE_DIR / "bardeen/record.har"
        csv_file = ARCHIVE_DIR / "bardeen.csv"

        await scraper.playwright.page.route_from_har(
            har=har_file,
            url="*/**",
            update=True,
        )

        await scraper.summarize(
            ctx=DebugContext(),
            output_file=csv_file,
            **configs["bardeen"],
        )


async def archive_retool():
    async with Scraper(headless=False, batch_size=10) as scraper:
        har_file = ARCHIVE_DIR / "retool/record.har"
        csv_file = ARCHIVE_DIR / "retool.csv"

        await scraper.playwright.page.route_from_har(
            har=har_file,
            url="*/**/templates.json",
            update=True,
        )

        await scraper.summarize(
            ctx=DebugContext(),
            output_file=csv_file,
            **configs["retool"],
        )


async def archive_ifttt():
    async with Scraper(headless=False, batch_size=10) as scraper:
        har_file = ARCHIVE_DIR / "ifttt/record.har"
        csv_file = ARCHIVE_DIR / "ifttt.csv"

        await scraper.playwright.page.route_from_har(
            har=har_file,
            url="*/**",
            update=True,
        )

        await scraper.summarize(
            ctx=DebugContext(),
            output_file=csv_file,
            **configs["ifttt"],
        )


async def archive_zapier():
    async with Scraper(headless=False, batch_size=10) as scraper:
        har_file = ARCHIVE_DIR / "zapier/record.har"
        csv_file = ARCHIVE_DIR / "zapier.csv"

        await scraper.playwright.page.route_from_har(
            har=har_file,
            url="*/**",
            update=True,
        )

        await scraper.summarize(
            ctx=DebugContext(),
            output_file=csv_file,
            **configs["zapier"],
        )


async def main():
    await asyncio.gather(
        archive_bardeen(),
        archive_retool(),
        archive_ifttt(),
        archive_zapier(),
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

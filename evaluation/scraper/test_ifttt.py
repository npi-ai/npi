import pathlib
import tempfile

from csv_diff import load_csv, compare

from npiai.utils.test_utils import DebugContext
from npiai.tools.web.scraper import Scraper

from configs import configs

ARCHIVE_DIR = pathlib.Path(__file__).parent / "archives"


async def test_ifttt_scraper():
    async with Scraper(headless=False, batch_size=10) as scraper:
        har_file = ARCHIVE_DIR / "ifttt/record.har"
        example_csv_file = ARCHIVE_DIR / "ifttt.csv"
        output_csv_file = pathlib.Path(tempfile.gettempdir()) / "ifttt.csv"

        print(f"output csv: {output_csv_file}")

        await scraper.playwright.context.set_offline(True)
        await scraper.playwright.page.route_from_har(
            har=har_file,
            url="*/**",
            update=False,
        )

        await scraper.summarize(
            ctx=DebugContext(),
            output_file=output_csv_file,
            **configs["ifttt"],
        )

        diff = compare(
            load_csv(open(example_csv_file), key="URL"),
            load_csv(open(output_csv_file), key="URL"),
        )

        assert not diff["added"]
        assert not diff["removed"]
        assert not diff["changed"]
        assert not diff["columns_added"]
        assert not diff["columns_removed"]
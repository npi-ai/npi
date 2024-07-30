import json
import os
import re
import tempfile
import pathlib
from typing import Literal

from playwright.async_api import TimeoutError, Error, Locator
from markdownify import MarkdownConverter
from slugify import slugify

from npiai import function, BrowserTool
from npiai.context import Context
from npiai.core.browser import NavigatorAgent
from npiai.utils import logger
from npiai.error.auth import UnauthorizedError

__SYSTEM_PROMPT__ = """
You are a Twitter Agent helping user retrieve and manage tweets. 

For any given task, you should first check if you are on the correct page. If not, you should use the navigator to go to the target page. 

For any action regarding posting a tweet or deleting a tweet, you should ask for user confirmation before proceeding. Otherwise, you should not stop until the task is complete.

For tasks requiring retrieval of the page contents, you may call the `get_text()` tool if no other suitable tool is available.

Note that the navigator is designed to finish arbitrary tasks by simulating user inputs, you may use it as the last resort to fulfill the task if all other tools are not able to complete the task. In this case, you may also give the navigator a rough plan as the hint.

However, the navigator is unable to retrieve the content of the tweets. If the task includes the analysis of a specific tweet, you should break it into several subtasks and coordinate tools to finish it. For example:

Task: reply to the latest tweet of @Dolphin_Wood

Steps:
1. goto_profile({ "username": "Dolphin_Wood" })
2. get_tweets({ "max_results": 1 })
3. open_tweet({ "url": "{{tweet_url}}" })
4. navigator({ "task": "Reply to current tweet with {{reply_content}}. Ask for user confirmation before posting." })

Task: get the last 10 tweets by @Dolphin_Wood

Steps:
1. goto_profile({ "username": "Dolphin_Wood" })
2. get_tweets({ "max_results": 10 })
3. Repeat the following steps until 10 tweets are found. Remember that you should exclude the pinned tweet.
  3.1. load_more_tweets()
  3.2. get_tweets({ "max_results": 10 })
"""

__ROUTES__ = {"login": "https://x.com/", "home": "https://x.com/home"}

from npiai.llm import LLM


class ImageFilterConverter(MarkdownConverter):
    def process_text(self, el):
        text = el.text

        if text == "Quote":
            return "\nQuote Tweet: "

        # remove messages inside the video component
        if el.find_parent(
            name="div", attrs={"data-testid": re.compile(r"videoComponent|tweetPhoto")}
        ):
            return ""

        parent = el.find_parent(
            name="div", attrs={"data-testid": re.compile(r"reply|retweet|like")}
        )

        if not parent:
            return super().process_text(el)

        count = text or "0"
        # annotate footer icons
        match parent.attrs.get("data-testid"):
            case "reply":
                return f" Replies: {count} "
            case "retweet":
                return f" Retweets: {count} "
            case "like":
                return f" Likes: {count} "
            case _:
                return super().process_text(el)

    def convert_a(self, el, text, convert_as_inline):
        if re.search(r"analytics", el.attrs.get("href", "")):
            return f' Views: {el.text or "0"}'
        return super().convert_a(el, text, convert_as_inline)

    def convert_img(self, el, text, convert_as_inline):
        src = el.attrs.get("src", "")
        # remove profile/card pictures
        if re.search(r"profile_images|card_img", src):
            return ""
        # remove emoji images
        if re.search(r"emoji", src):
            return el.attrs.get("alt")

        return super().convert_img(el, text, convert_as_inline)


def html_to_md(html: str, **options) -> str:
    return ImageFilterConverter(**options).convert(html)


class Twitter(BrowserTool):
    name = "twitter"
    description = "retrieve and manage tweets"
    system_prompt = __SYSTEM_PROMPT__

    _username: str
    _password: str

    def __init__(
        self,
        username: str = None,
        password: str = None,
        navigator_llm: LLM = None,
        headless: bool = True,
    ):
        super().__init__(
            headless=headless,
        )

        self._username = username or os.environ.get("TWITTER_USERNAME", None)
        self._password = password or os.environ.get("TWITTER_PASSWORD", None)
        self.ctx = None

        self.add_tool(NavigatorAgent(llm=navigator_llm, playwright=self.playwright))

    async def start(self):
        if self._username is None:
            raise UnauthorizedError("No Twitter username provided.")

        if self._password is None:
            raise UnauthorizedError("No Twitter password provided.")

        if not self._started:
            await super().start()
            await self._login(self.ctx)

    async def _login(self, ctx: Context | None = None):
        state_file = (
            pathlib.Path(tempfile.gettempdir())
            / f"{slugify(self._username)}/twitter_state.json"
        )
        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                state = json.load(f)
                await self.playwright.context.add_cookies(state["cookies"])
            await self.playwright.page.goto(__ROUTES__["home"])
            try:
                # validate cookies
                await self.playwright.page.wait_for_url(__ROUTES__["home"])
                logger.debug("Twitter cookies restored.")
                return
            except TimeoutError:
                # cookies expired, continue login process
                logger.debug("Twitter cookies expired. Continue login process.")

        await self.playwright.page.goto(__ROUTES__["login"])
        await self.playwright.page.get_by_test_id("loginButton").click()
        await self.playwright.page.get_by_label("Phone, email, or username").fill(
            self._username
        )
        await self.playwright.page.get_by_role("button", name="Next").click()

        # check if additional credentials (i.e, username) is required
        await self._check_additional_credentials(ctx)

        await self.playwright.page.get_by_label("Password", exact=True).fill(
            self._password
        )
        await self.playwright.page.get_by_test_id("LoginForm_Login_Button").click()

        # check again if additional credentials (i.e, phone number) is required
        await self._check_additional_credentials(ctx)

        # now we should be directed to twitter home
        await self.playwright.page.wait_for_url(__ROUTES__["home"])

        # save state
        save_dir = os.path.dirname(state_file)
        os.makedirs(save_dir, exist_ok=True)
        await self.playwright.context.storage_state(path=state_file)

    async def _get_additional_cred_input(self) -> Locator | None:
        await self.playwright.page.wait_for_timeout(1000)
        cred_input = self.playwright.page.get_by_test_id("ocfEnterTextTextInput")

        try:
            if await cred_input.count() != 0:
                return cred_input
        except Error:
            return None

    async def _check_additional_credentials(self, ctx: Context | None = None):
        cred_input = await self._get_additional_cred_input()

        if cred_input:
            label = self.playwright.page.locator(
                'label:has(input[data-testid="ocfEnterTextTextInput"])'
            )
            cred_name = await label.text_content()
            cred = await self._request_additional_credentials(cred_name, ctx)
            await cred_input.fill(cred)
            await self.playwright.page.get_by_test_id("ocfEnterTextNextButton").click()

            if await self._get_additional_cred_input() is not None:
                raise UnauthorizedError(
                    "Unable to login to Twitter. Please try again with the correct credentials."
                )

    async def _request_additional_credentials(
        self, cred_name: str, ctx: Context | None = None
    ) -> str:
        if ctx is None:
            raise UnauthorizedError(
                f"Unable to login to Twitter. Please replace username with {cred_name} and try again."
            )

        return await self.hitl.input(
            ctx,
            self.name,
            f"Please enter {cred_name} to continue the login process.",
        )

    @function
    async def search(
        self, query: str, sort_by: Literal["hottest", "latest"] = "hottest"
    ):
        """
        Search Twitter for tweets or users matching the given query.

        Args:
            query: Twitter search query.
            sort_by: Sort results by this parameter. Default is "hottest".
        """
        await self.playwright.page.goto("https://x.com/explore")
        search_input = self.playwright.page.get_by_test_id("SearchBox_Search_Input")
        await search_input.fill(query)
        await search_input.press("Enter")

        if sort_by == "latest":
            await self.playwright.page.wait_for_timeout(1000)
            await self.playwright.page.get_by_role("tab", name="Latest").click()

        return f"The search result page is opened. Please use other tools to retrieve the results. Current page: {await self.get_page_title()}"

    @function
    async def goto_profile(self, username: str):
        """
        Goto Twitter user's profile page.

        Args:
            username: Twitter username.
        """
        username = username.replace("@", "")
        await self.playwright.page.goto(f"https://x.com/{username}")

        return f"The profile page for user {username} is opened. Current page: {await self.get_page_title()}"

    @function
    async def goto_notifications(self):
        """Goto Twitter user's notifications page."""
        await self.playwright.page.goto("https://x.com/notifications/mentions")

        return f"The notifications page is opened. Current page: {await self.get_page_title()}"

    @function
    async def reply(self, url: str, content: str):
        """
        Open the given tweet and reply to it.

        Args:
            url: URL of the tweet you want to reply to.
            content: Reply content.
        """
        await self.playwright.page.goto(url)
        reply_input = self.playwright.page.get_by_test_id("tweetTextarea_0")
        await reply_input.click()
        await self.playwright.page.wait_for_timeout(300)
        await reply_input.fill(content)
        await self.playwright.page.get_by_test_id("tweetButtonInline").click()

        return f"Replied to tweet {url} with content: {content}"

    @function
    async def get_current_page(self):
        """Get the title and url of the current page."""
        result = {
            "title": await self.playwright.page.title(),
            "url": self.playwright.page.url,
        }
        return json.dumps(result, ensure_ascii=False)

    @function
    async def get_tweets(self, max_results: int = -1) -> str:
        """
        Retrieve tweets on the current page.
        You should ensure you are on the correct page (home, user profile, etc.) before calling this tool.

        Args:
            max_results: Maximum number of tweets to return. Pass -1 for no limit.
        """
        try:
            # match unvisited tweets only
            tweets = self.playwright.page.locator(
                '[data-testid="tweet"]:not([data-visited])'
            )
            await tweets.first.wait_for(state="attached", timeout=180_000)

            logger.debug(f"{await tweets.count()} tweets found.")
        except TimeoutError:
            return "No tweets found."

        results = []

        for tweet in await tweets.all():
            try:
                # skip ads
                if await tweet.get_by_text("Ad", exact=True).count() > 0:
                    logger.debug(f"Skipping ad: {await tweet.text_content()}")
                    continue
                # skip spaces
                if (
                    await tweet.get_by_role(
                        "button", name="Play recording", exact=True
                    ).count()
                    > 0
                ):
                    logger.debug(f"Skipping space: {await tweet.text_content()}")
                    continue
                # author = await tweet.get_by_test_id('User-Name').first.text_content()
                # content = author + ': ' + await tweet.get_by_test_id('tweetText').first.text_content()
                # # extract social context
                # social_context = tweet.get_by_test_id('socialContext')
                # if await social_context.count() == 1:
                #     content = await social_context.text_content() + '\n' + content
                # # extract media
                # media = tweet.locator(
                #     '[data-testid="videoPlayer"]:has([src]), \
                #      [data-testid="tweetPhoto"]:not(:has([data-testid="videoPlayer"])):has([src])'
                # )
                # if await media.count() > 0:
                #     content += ' ' + await media.evaluate_all(
                #         """elems => {
                #             return elems.map(el => {
                #                 const mediaType = el.getAttribute('data-testid') === 'tweetPhoto' ? 'image' : 'video';
                #                 const src = el.querySelector('[src]')?.src;
                #                 return `![${mediaType}][${src}]`;
                #             }).join(' ')
                #         }"""
                #     )
                # # extract retweet
                # retweet = tweet.locator('div[role="link"]:has([data-testid="tweetText"])')
                # if await retweet.count() == 1:
                #     content += '\n Retweet: ' + await retweet.text_content()

                # extract link
                link = await tweet.locator('a[href*="/status/"]').first.get_attribute(
                    "href"
                )
                results.append(
                    {
                        "link": f"https://x.com{link}",
                        "content": html_to_md(await tweet.inner_html()),
                    }
                )
            except TimeoutError as e:
                logger.error(e)
            finally:
                if -1 < max_results <= len(results):
                    break

        # mark as visited
        await tweets.evaluate_all(
            'elems => elems.forEach(el => el.setAttribute("data-visited", "true"))'
        )

        logger.debug(
            f"{len(results)} tweets retrieved: {json.dumps(results, indent=2, ensure_ascii=False)}"
        )

        return json.dumps(results, ensure_ascii=False)

    @function
    async def load_more_tweets(self) -> str:
        """Scroll to bottom of the page to load more tweets."""
        if not await self.is_scrollable():
            return "All tweets loaded. No more tweets."

        await self.playwright.page.evaluate(
            """() => {
                const tweets = document.querySelectorAll('[data-testid="tweet"]');
                tweets[tweets.length - 1]?.scrollIntoView();
            }"""
        )

        await self.playwright.page.wait_for_timeout(3000)

        return "More tweets loaded."

    @function
    async def open_tweet(self, url: str) -> str:
        """
        Open a tweet with the given URL.

        Args:
            url: URL of the tweet you want to open.
        """
        await self.playwright.page.goto(url, timeout=10_000)

        return f"Tweet opened. Current URL: {await self.get_page_url()}, page title: {await self.get_page_title()}"


__all__ = ["Twitter"]

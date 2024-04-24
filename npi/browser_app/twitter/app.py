import json
import os
import re
from playwright.async_api import TimeoutError
from markdownify import MarkdownConverter

from npi.core import BrowserApp, npi_tool
from npi.utils import logger
from npi.browser_app.navigator import Navigator
from npi.config import config
from .schema import *

__SYSTEM_PROMPT__ = """
You are a Twitter Agent helping user retrieve and manage tweets. 

For any given task, you should first check if you are on the correct page. If not, you should use the navigator to go to the target page. 

For any action regarding posting a tweet or deleting a tweet, should ask for user confirmation before proceeding.

Note that the navigator is designed to finish arbitrary tasks by simulating user inputs, you may use it as the last resort to fulfill the task if all other tools are not able to complete the task. In this case, you may also give the navigator a rough plan as the hint.

However, the navigator is unable to retrieve the content of the tweets. If the task includes the analysis of a specific tweet, you should break it into several subtasks and coordinate tools to finish it. For example:

Task: reply to the latest tweet of @Dolphin_Wood

Steps:
1. navigator({ "task": "Go to the profile page of @Dolphin_Wood" })
2. get_tweets({ "max_results": 1 })
3. open_tweet({ "url": "{{tweet_url}}" })
4. navigator({ "task": "Reply to current tweet with {{reply_content}}. Ask for user confirmation before posting." })
"""

__ROUTES__ = {
    'login': 'https://twitter.com/',
    'home': 'https://twitter.com/home'
}

from ...error.auth import UnauthorizedError


class ImageFilterConverter(MarkdownConverter):
    def process_text(self, el):
        text = el.text

        if text == 'Quote':
            return '\nQuote Tweet: '

        # remove messages inside the video component
        if el.find_parent(name='div', attrs={'data-testid': re.compile(r'videoComponent|tweetPhoto')}):
            return ''

        parent = el.find_parent(name='div', attrs={'data-testid': re.compile(r'reply|retweet|like')})

        if not parent:
            return super().process_text(el)

        count = text or '0'
        # annotate footer icons
        match parent.attrs.get('data-testid'):
            case 'reply':
                return f' Replies: {count} '
            case 'retweet':
                return f' Retweets: {count} '
            case 'like':
                return f' Likes: {count} '
            case _:
                return super().process_text(el)

    def convert_a(self, el, text, convert_as_inline):
        if re.search(r'analytics', el.attrs.get('href', '')):
            return f' Views: {el.text or "0"}'
        return super().convert_a(el, text, convert_as_inline)

    def convert_img(self, el, text, convert_as_inline):
        src = el.attrs.get('src', '')
        # remove profile/card pictures
        if re.search(r'profile_images|card_img', src):
            return ''
        # remove emoji images
        if re.search(r'emoji', src):
            return el.attrs.get('alt')

        return super().convert_img(el, text, convert_as_inline)


def html_to_md(html: str, **options) -> str:
    return ImageFilterConverter(**options).convert(html)


class Twitter(BrowserApp):
    creds: config.TwitterCredentials
    state_file: str = './credentials/twitter_state.json'

    def __init__(self, llm=None, headless: bool = True):
        creds = config.get_twitter_credentials()

        if creds is None:
            raise UnauthorizedError("Twitter credentials are not found, please use `npi auth twitter` first")

        super().__init__(
            name='twitter',
            description='retrieve and manage tweets',
            system_role=__SYSTEM_PROMPT__,
            llm=llm,
            headless=headless,
        )

        self.creds = creds

        self.register(Navigator(playwright=self.playwright))

    async def start(self):
        if not self._started:
            await super().start()
            await self._login()

    async def _login(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                await self.playwright.context.add_cookies(state['cookies'])
            await self.playwright.page.goto(__ROUTES__['home'])
            try:
                # validate cookies
                await self.playwright.page.wait_for_url(__ROUTES__['home'], timeout=10_000)
                logger.debug('Twitter cookies restored.')
                return
            except TimeoutError:
                # cookies expired, continue login process
                logger.debug('Twitter cookies expired. Continue login process.')

        await self.playwright.page.goto(__ROUTES__['login'])
        await self.playwright.page.get_by_test_id('loginButton').click()
        await self.playwright.page.get_by_label('Phone, email, or username').fill(self.creds.username)
        await self.playwright.page.get_by_role('button', name='Next').click()
        await self.playwright.page.get_by_label('Password', exact=True).fill(self.creds.password)
        await self.playwright.page.get_by_test_id('LoginForm_Login_Button').click()
        await self.playwright.page.wait_for_url(__ROUTES__['home'], timeout=10_000)

        # save state
        await self.playwright.context.storage_state(path=self.state_file)

    @npi_tool
    async def get_current_page(self):
        """Get the title and url of the current page."""
        result = {
            'title': await self.playwright.page.title(),
            'url': self.playwright.page.url,
        }
        return json.dumps(result, ensure_ascii=False)

    @npi_tool
    async def get_tweets(self, params: GetTweetsParameters) -> str:
        """
        Retrieve tweets on the current page.
        You should ensure you are on the correct page (home, user profile, etc.) before calling this tool.
        """
        scrollable = await self.is_scrollable()

        if not scrollable:
            # no more tweets
            return 'No more tweets'

        results = []

        # match unvisited tweets only
        tweets = self.playwright.page.locator('[data-testid="tweet"]:not([data-visited])')
        await tweets.first.wait_for(state='attached', timeout=10_000)

        logger.debug(f'{await tweets.count()} tweets found.')

        for tweet in await tweets.all():
            try:
                # skip ads
                if await tweet.get_by_text('Ad', exact=True).count() > 0:
                    logger.debug(f'Skipping ad: {await tweet.text_content()}')
                    continue
                # skip spaces
                if await tweet.get_by_role('button', name='Play recording', exact=True).count() > 0:
                    logger.debug(f'Skipping space: {await tweet.text_content()}')
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
                link = await tweet.locator('a[href*="/status/"]').first.get_attribute('href')
                results.append(
                    {
                        'link': f'https://twitter.com{link}',
                        'content': html_to_md(await tweet.inner_html()),
                    }
                )
            except TimeoutError as e:
                logger.error(e)
            finally:
                if -1 < params.max_results <= len(results):
                    break

        # mark as visited
        await tweets.evaluate_all('elems => elems.forEach(el => el.setAttribute("data-visited", "true"))')

        logger.debug(f'{len(results)} tweets retrieved: {json.dumps(results, indent=2, ensure_ascii=False)}')

        return json.dumps(results, ensure_ascii=False)

    @npi_tool
    async def load_more_tweets(self) -> str:
        """Scroll to bottom of the page to load more tweets."""
        if not await self.is_scrollable():
            return 'All tweets loaded. No more tweets.'

        await self.playwright.page.evaluate(
            """() => {
                const tweets = document.querySelectorAll('[data-testid="tweet"]');
                tweets[tweets.length - 1]?.scrollIntoView();
            }"""
        )

        await self.playwright.page.wait_for_timeout(3000)

        return 'More tweets loaded.'

    @npi_tool
    async def open_tweet(self, params: OpenTweetParameters) -> str:
        """Open a tweet with the given URL."""
        await self.playwright.page.goto(params.url, timeout=10_000)

        return f'Tweet opened. Current URL: {await self.get_page_url()}, page title: {await self.get_page_title()}'


__all__ = ['Twitter']

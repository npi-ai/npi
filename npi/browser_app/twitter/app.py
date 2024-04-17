import json
import os
from playwright.async_api import TimeoutError

from npi.core import BrowserApp, npi_tool
from npi.utils import logger
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


class Twitter(BrowserApp):
    # TODO: configurable credentials
    secret_file: str = './credentials/twitter.json'
    state_file: str = './credentials/twitter_state.json'

    def __init__(self, llm=None, headless: bool = True):
        super().__init__(
            name='twitter',
            description='retrieve and manage tweets',
            system_role=__SYSTEM_PROMPT__,
            llm=llm,
            headless=headless,
            use_navigator=True,
        )

    async def start(self):
        await super().start()
        await self._login()

    async def _login(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                await self.context.add_cookies(state['cookies'])
            await self.page.goto(__ROUTES__['home'])
            try:
                # validate cookies
                await self.page.wait_for_url(__ROUTES__['home'], timeout=10_000)
                logger.debug('Twitter cookies restored.')
                return
            except TimeoutError:
                # cookies expired, continue login process
                logger.debug('Twitter cookies expired. Continue login process.')

        credentials = json.load(open(self.secret_file))
        await self.page.goto(__ROUTES__['login'])
        await self.page.get_by_test_id('loginButton').click()
        await self.page.get_by_label('Phone, email, or username').fill(credentials['username'])
        await self.page.get_by_role('button', name='Next').click()
        await self.page.get_by_label('Password', exact=True).fill(credentials['password'])
        await self.page.get_by_test_id('LoginForm_Login_Button').click()
        await self.page.wait_for_url(__ROUTES__['home'], timeout=10_000)

        # save state
        await self.context.storage_state(path=self.state_file)

    @npi_tool
    async def get_current_page(self):
        """Get the title and url of the current page."""
        result = {
            'title': await self.page.title(),
            'url': self.page.url,
        }
        return json.dumps(result, ensure_ascii=False)

    @npi_tool
    async def get_tweets(self, params: GetTweetsParameters) -> str:
        """Retrieve tweets on the current page. You should ensure you are on the correct page (home, user profile, etc.) before calling this tool."""
        scrollable = await self.navigator.is_scrollable()

        if not scrollable:
            # no more tweets
            return 'No more tweets'

        results = []

        tweets = self.page.get_by_test_id('tweet')
        await tweets.first.wait_for(state='attached', timeout=10_000)

        logger.debug(f'{await tweets.count()} tweets found.')

        for tweet in await tweets.all():
            try:
                author = await tweet.get_by_test_id('User-Name').first.text_content()
                content = author + ': ' + await tweet.get_by_test_id('tweetText').first.text_content()
                # extract media
                media = tweet.locator(
                    '[data-testid="videoPlayer"]:has([src]), \
                     [data-testid="tweetPhoto"]:not(:has([data-testid="videoPlayer"])):has([src])'
                )
                if await media.count() > 0:
                    content += ' ' + await media.evaluate_all(
                        """elems => {
                            return elems.map(el => {
                                const mediaType = el.getAttribute('data-testid') === 'tweetPhoto' ? 'image' : 'video';
                                const src = el.querySelector('[src]')?.src;
                                return `![${mediaType}][${src}]`;
                            }).join(' ')
                        }"""
                    )
                # extract retweet
                retweet = tweet.locator('div[role="link"]:has([data-testid="tweetText"])')
                if await retweet.count() == 1:
                    content += '\n Retweet: ' + await retweet.text_content()

                # extract link
                link = await tweet.locator('a:has(time)').first.get_attribute('href')
                results.append(
                    {
                        'link': f'https://twitter.com{link}',
                        'content': content
                    }
                )
            except TimeoutError:
                ...
            finally:
                if -1 < params.max_results <= len(results):
                    break

        logger.debug(f'Tweets retrieved: {json.dumps(results, indent=2, ensure_ascii=False)}')

        return json.dumps(results, ensure_ascii=False)

    @npi_tool
    async def load_more_tweets(self) -> str:
        """Scroll to bottom of the page to load more tweets."""
        scroll_y_old = await self.page.evaluate('() => window.scrollY')

        await self.page.evaluate('() => window.scrollTo(window.scrollX, Number.MAX_SAFE_INTEGER)')

        scroll_y_new = await self.page.evaluate('() => window.scrollY')

        if scroll_y_old == scroll_y_new:
            return 'All tweets loaded. No more tweets.'

        await self.page.wait_for_timeout(3000)

        return 'More tweets loaded.'

    @npi_tool
    async def open_tweet(self, params: OpenTweetParameters) -> str:
        """Open a tweet with the given URL."""
        await self.page.goto(params.url, timeout=10_000)

        return f'Tweet opened. Current URL: {self.page.url}, page title: {await self.page.title()}'
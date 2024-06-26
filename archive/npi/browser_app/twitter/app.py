import json
import os
import re

from npiai_proto import api_pb2
from playwright.async_api import TimeoutError
from markdownify import MarkdownConverter

from npi.core import BrowserApp, npi_tool
from npi.utils import logger
from npi.browser_app.navigator import Navigator
from npi.config import config
from npi.error.auth import UnauthorizedError
from npi.core.callback import callback
from npi.core.thread import Thread
from .schema import *

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

__ROUTES__ = {
    'login': 'https://x.com/',
    'home': 'https://x.com/home'
}


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

    async def start(self, thread: Thread = None):
        if not self._started:
            await super().start(thread)
            await self._login(thread)

    async def _login(self, thread: Thread):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                await self.playwright.context.add_cookies(state['cookies'])
            await self.playwright.page.goto(__ROUTES__['home'])
            try:
                # validate cookies
                await self.playwright.page.wait_for_url(__ROUTES__['home'])
                logger.debug('Twitter cookies restored.')
                return
            except TimeoutError:
                # cookies expired, continue login process
                logger.debug('Twitter cookies expired. Continue login process.')

        await self.playwright.page.goto(__ROUTES__['login'])
        await self.playwright.page.get_by_test_id('loginButton').click()
        await self.playwright.page.get_by_label('Phone, email, or username').fill(self.creds.username)
        await self.playwright.page.get_by_role('button', name='Next').click()

        # check if additional credentials (i.e, username) is required
        await self._check_additional_credentials(thread)

        await self.playwright.page.get_by_label('Password', exact=True).fill(self.creds.password)
        await self.playwright.page.get_by_test_id('LoginForm_Login_Button').click()

        # check again if additional credentials (i.e, phone number) is required
        await self._check_additional_credentials(thread)

        # now we should be directed to twitter home
        await self.playwright.page.wait_for_url(__ROUTES__['home'])

        # save state
        save_dir = os.path.dirname(self.state_file)
        os.makedirs(save_dir, exist_ok=True)
        await self.playwright.context.storage_state(path=self.state_file)

        await thread.send_msg(callback.Callable('Logged in to Twitter'))

    async def _check_additional_credentials(self, thread: Thread):
        await self.playwright.page.wait_for_timeout(1000)
        cred_input = self.playwright.page.get_by_test_id("ocfEnterTextTextInput")
        if await cred_input.count() != 0:
            label = self.playwright.page.locator('label:has(input[data-testid="ocfEnterTextTextInput"])')
            cred_name = await label.text_content()
            cred = await self._request_additional_credentials(thread, cred_name)
            await cred_input.fill(cred)
            await self.playwright.page.get_by_test_id("ocfEnterTextNextButton").click()

            await self.playwright.page.wait_for_timeout(1000)
            if await cred_input.count() != 0:
                raise UnauthorizedError('Unable to login to Twitter. Please try again with the correct credentials.')

    @staticmethod
    async def _request_additional_credentials(thread: Thread, cred_name: str) -> str:
        if thread is None:
            raise Exception('`thread` must be provided to request username')

        cb = callback.Callable(
            action=api_pb2.ActionRequiredResponse(
                type=api_pb2.ActionType.INFORMATION,  # TODO(wenfeng) Add type of Form
                message=f'Please enter {cred_name} to continue the login process.',
            ),
        )
        cb.action.action_id = cb.id()
        await thread.send_msg(cb=cb)
        res = await cb.wait()
        return res.result.action_result

    @npi_tool
    async def search(self, params: SearchParameters):
        """Search Twitter for tweets or users matching the given query."""
        await self.playwright.page.goto('https://x.com/explore')
        search_input = self.playwright.page.get_by_test_id('SearchBox_Search_Input')
        await search_input.fill(params.query)
        await search_input.press('Enter')

        if params.sort_by == 'latest':
            await self.playwright.page.wait_for_timeout(1000)
            await self.playwright.page.get_by_role("tab", name="Latest").click()

        return f'The search result page is opened. Please use other tools to retrieve the results. Current page: {await self.get_page_title()}'

    @npi_tool
    async def goto_profile(self, params: GotoProfileParameters):
        """Goto Twitter user's profile page."""
        username = params.username.replace('@', '')
        await self.playwright.page.goto(f'https://x.com/{username}')

        return f'The profile page for user {params.username} is opened. Current page: {await self.get_page_title()}'

    @npi_tool
    async def goto_notifications(self):
        """Goto Twitter user's notifications page."""
        await self.playwright.page.goto('https://x.com/notifications/mentions')

        return f'The notifications page is opened. Current page: {await self.get_page_title()}'

    @npi_tool
    async def reply(self, params: ReplyParameters):
        """Open the given tweet and reply to it."""
        await self.playwright.page.goto(params.url)
        reply_input = self.playwright.page.get_by_test_id('tweetTextarea_0')
        await reply_input.click()
        await self.playwright.page.wait_for_timeout(300)
        await reply_input.fill(params.content)
        await self.playwright.page.get_by_test_id('tweetButtonInline').click()

        return f'Replied to tweet {params.url} with content: {params.content}'

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
        await tweets.first.wait_for(state='attached', timeout=180_000)

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
                        'link': f'https://x.com{link}',
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

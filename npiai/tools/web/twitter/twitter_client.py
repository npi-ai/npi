import json
import os
import pathlib
import tempfile

from playwright.async_api import TimeoutError, Error, Locator
from slugify import slugify

from npiai.context import Context
from npiai.core import PlaywrightContext
from npiai.error.auth import UnauthorizedError
from npiai.utils import logger

__ROUTES__ = {"login": "https://x.com/", "home": "https://x.com/home"}


class TwitterClient:
    playwright: PlaywrightContext

    _ctx: Context
    _username: str
    _password: str

    def __init__(
        self,
        ctx: Context,
        username: str,
        password: str,
        playwright: PlaywrightContext | None = None,
        headless: bool = True,
    ):
        self._ctx = ctx
        self._username = username
        self._password = password
        self.playwright = playwright or PlaywrightContext(headless=headless)

    async def login(
        self,
    ):
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
        await self._check_additional_credentials()

        await self.playwright.page.get_by_label("Password", exact=True).fill(
            self._password
        )
        await self.playwright.page.get_by_test_id("LoginForm_Login_Button").click()

        # check again if additional credentials (i.e, phone number) is required
        await self._check_additional_credentials()

        # now we should be directed to twitter home
        await self.playwright.page.goto(__ROUTES__["home"])
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

    async def _check_additional_credentials(self):
        cred_input = await self._get_additional_cred_input()

        if cred_input:
            label = self.playwright.page.locator(
                'label:has(input[data-testid="ocfEnterTextTextInput"])'
            )
            cred_name = await label.text_content()
            cred = await self._request_additional_credentials(cred_name)
            await cred_input.fill(cred)
            await self.playwright.page.get_by_test_id("ocfEnterTextNextButton").click()

            if await self._get_additional_cred_input() is not None:
                raise UnauthorizedError(
                    "Unable to login to Twitter. Please try again with the correct credentials."
                )

    async def _request_additional_credentials(
        self,
        cred_name: str,
    ) -> str:
        if self._ctx is None:
            raise UnauthorizedError(
                f"Unable to login to Twitter. Please replace username with {cred_name} and try again."
            )

        return await self._ctx.hitl.input(
            tool_name="TwitterClient",
            message=f"Please enter {cred_name} to continue the login process.",
        )

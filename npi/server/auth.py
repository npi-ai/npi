"""the http server for NPI backend"""

import json
from google_auth_oauthlib.flow import InstalledAppFlow, Flow

from pydantic import BaseModel

from npi.config import config
from npi.app.google import GoogleCalendar, Gmail

__SCOPE = {
    "gmail": Gmail.SCOPE,
    "calendar": GoogleCalendar.SCOPE
}


class GoogleAuthRequest(BaseModel):
    """request for google auth"""
    secrets: str
    app: str


class GithubAuthRequest(BaseModel):
    access_token: str


class DiscordAuthRequest(BaseModel):
    access_token: str


class TwitterAuthRequest(BaseModel):
    username: str
    password: str


class TwilioAuthRequest(BaseModel):
    from_phone_number: str
    account_sid: str
    auth_token: str


STATE = {}


async def auth_google(req: GoogleAuthRequest):
    """the core api of NPI"""
    if req.app not in __SCOPE:
        raise ValueError(f"app {req.app} is not supported")
    secret_cfg = json.loads(req.secrets)
    flow = InstalledAppFlow.from_client_config(
        client_config=secret_cfg,
        scopes=__SCOPE[req.app],
        redirect_uri="http://localhost:19141/auth/google/callback",
    )
    url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent'
    )
    STATE[state] = {
        "secret": secret_cfg,
        "app": req.app,
    }
    return {'url': url}


async def google_callback(state: str, code: str):
    if state not in STATE:
        raise ValueError(f"invalid state {state}")

    cfg = STATE[state]
    flow = Flow.from_client_config(
        client_config=cfg["secret"],
        scopes=__SCOPE[cfg["app"]],
        redirect_uri="http://localhost:19141/auth/google/callback",
        state=state,
    )

    flow.fetch_token(code=code)
    credentials = flow.credentials

    if cfg["app"] == "calendar":
        config.set_google_calendar_credentials(cfg["secret"], credentials)
    else:
        config.set_gmail_credentials(cfg["secret"], credentials)
    return 'Success, close the window.'


async def auth_github(req: GithubAuthRequest):
    config.set_github_credentials(req.access_token)


async def auth_discord(req: DiscordAuthRequest):
    config.set_discord_credentials(req.access_token)


async def auth_twitter(req: TwitterAuthRequest):
    config.set_twitter_credentials(req.username, req.password)


async def auth_twilio(req: TwilioAuthRequest):
    config.set_twilio_credentials(account_sid=req.account_sid, auth_token=req.auth_token,
                                  from_phone_number=req.from_phone_number)


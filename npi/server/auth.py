"""the http server for NPI backend"""

import json
from fastapi import FastAPI, responses
from google_auth_oauthlib.flow import InstalledAppFlow, Flow

from pydantic import BaseModel

from npi.config import config
from npi.app.google import GoogleCalendar, Gmail

app = FastAPI()

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


STATE = {}


@app.post("/auth/google")
async def auth_google(req: GoogleAuthRequest):
    """the core api of NPI"""
    if req.app not in __SCOPE:
        return responses.Response("invalid app", status_code=400)
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


@app.get("/auth/google/callback")
async def auth_google(state: str, code: str):
    """the core api of NPI"""

    if state not in STATE:
        return responses.FileResponse("invalid state")

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


@app.post('/auth/github')
async def auth_github(req: GithubAuthRequest):
    config.set_github_credentials(req.access_token)
    return responses.Response(status_code=200)


@app.post('/auth/discord')
async def auth_discord(req: DiscordAuthRequest):
    config.set_discord_credentials(req.access_token)
    return responses.Response(status_code=200)


@app.post('/auth/twitter')
async def auth_twitter(req: TwitterAuthRequest):
    config.set_twitter_credentials(req.username, req.password)
    return responses.Response(status_code=200)


@app.get('/ping')
async def ping():
    return responses.Response(status_code=200)

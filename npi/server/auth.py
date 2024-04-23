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


STATE = {}


@app.post("/auth/google")
async def auth_google(req: GoogleAuthRequest):
    """the core api of NPI"""
    if req.app not in __SCOPE:
        return "Error: App not found"
    secret_cfg = json.loads(req.secrets)
    flow = InstalledAppFlow.from_client_config(
        client_config=secret_cfg,
        scopes=__SCOPE[req.app],
        redirect_uri="http://localhost:9141/auth/google/callback"
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
        redirect_uri="http://localhost:9141/auth/google/callback",
        state=state,
    )
    # flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    flow.fetch_token(code=code)
    credentials = flow.credentials
    file = GoogleCalendar.TOKEN_FILE if cfg["app"] == "calendar" else Gmail.TOKEN_FILE
    with open("/".join([config.get_project_root(), file]), "w", encoding="utf-8") as token:
        token.write(credentials.to_json())
    # return "Error: App not found"
    return "Success, close the window."

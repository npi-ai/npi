import os
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


def load_google_credentials(secret_file: str, token_file: str, scopes: List[str]):
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_file=secret_file, scopes=scopes
            )
            creds = flow.run_local_server(port=19140,redirect_uri_trailing_slash=False)
        # Save the credentials for the next run
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    return creds


def load_gmail_credentials(config_file: str | None = None):
    if config_file is None:
        config_file = os.getenv('CONFIG_FILE', ".")
    return load_google_credentials(
        secret_file='/'.join([config_file, 'credentials/google.json']),
        token_file='/'.join([config_file, 'credentials/gmail_token.json']),
        scopes=['https://mail.google.com/'],
    )


def load_google_calendar_credentials(config_file: str | None = None):
    if config_file is None:
        config_file = os.getenv('CONFIG_FILE', ".")
    return load_google_credentials(
        secret_file='/'.join([config_file, 'credentials/google.json']),
        token_file='/'.join([config_file, 'credentials/gc_token.json']),
        scopes=['https://www.googleapis.com/auth/calendar'],
    )

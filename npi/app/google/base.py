import os
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from npi.core import App


class GoogleApp(App):
    _scopes: List[str]
    _secret_file: str
    _token_file: str

    def __init__(
        self,
        name,
        description,
        system_role,
        llm=None,
        secret_file: str = None,
        token_file: str = None,
        scopes: List[str] = None
    ):
        super().__init__(name=name, description=description, system_role=system_role, llm=llm)
        self._secret_file = secret_file
        self._token_file = token_file
        self._scopes = scopes

    def _get_creds(self):
        creds = None
        if os.path.exists(self._token_file):
            creds = Credentials.from_authorized_user_file(self._token_file, self._scopes)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self._secret_file, self._scopes
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(self._token_file, "w", encoding="utf-8") as token:
                token.write(creds.to_json())

        return creds

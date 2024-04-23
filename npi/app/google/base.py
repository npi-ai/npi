import os
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from npi.core import App


class GoogleApp(App):
    _scopes: List[str]
    _token_file: str

    def __init__(
            self,
            name,
            description,
            system_role,
            llm=None,
            token_file: str = None,
            scopes: List[str] = None
    ):
        super().__init__(name=name, description=description, system_role=system_role, llm=llm)
        self._token_file = token_file
        self._scopes = scopes

    def _get_creds(self):
        if not os.path.exists(self._token_file):
            raise FileNotFoundError(f"Google token file not found, please use `npi connect google`")
        creds = Credentials.from_authorized_user_file(self._token_file, self._scopes)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise Exception("Google credentials are invalid, please use `npi connect google`")

        return creds

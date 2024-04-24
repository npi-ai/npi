import os
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from npi.core import App


class GoogleApp(App):
    _scopes: List[str]
    _creds: Credentials

    def __init__(
            self,
            name,
            description,
            system_role,
            creds,
            llm=None,
            scopes: List[str] = None
    ):
        super().__init__(name=name, description=description, system_role=system_role, llm=llm)
        self._creds = creds
        self._scopes = scopes

    def _get_creds(self):
        # creds = Credentials.from_authorized_user_info(self._creds, self._scopes)

        # If there are no (valid) credentials available, let the user log in.
        if not self._creds or not self._creds.valid:
            if self._creds and self._creds.expired and self._creds.refresh_token:
                self._creds.refresh(Request())
            else:
                raise Exception("Google credentials are invalid, please use `npi connect google`")

        return self._creds

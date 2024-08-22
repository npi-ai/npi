from google.oauth2.credentials import Credentials as GoogleCredentials
from oauth2client.client import OAuth2Credentials

from simplegmail import Gmail
from simplegmail.attachment import Attachment


class GmailClient(Gmail):
    def __init__(self, credentials: GoogleCredentials):
        oauth_creds = OAuth2Credentials(
            access_token=credentials.token,
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
            refresh_token=credentials.refresh_token,
            token_expiry=credentials.expiry,
            token_uri=credentials.token_uri,
            scopes=credentials.scopes,
            user_agent=None,
        )

        super().__init__(_creds=oauth_creds)

    def search_iterator(
        self,
        user_id: str = "me",
        query: str = "",
    ):
        """
        Iterate through search results

        Args:
            user_id: the user's email address. Default 'me', the authenticated
                user.
            query: a Gmail query to match.
        """

        page_token = None

        while True:
            response = (
                self.service.users()
                .messages()
                .list(
                    userId=user_id,
                    q=query,
                    maxResults=1,
                    pageToken=page_token,
                )
                .execute()
            )

            messages = response.get("messages", [])

            if not messages:
                break

            yield self._build_message_from_ref(
                user_id=user_id,
                message_ref=messages[0],
            )

            page_token = response.get("nextPageToken", None)

            if not page_token:
                break

    def download_attachment(self, attachment: Attachment): ...

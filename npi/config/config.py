import os
from dataclasses import dataclass

from npiai_proto import api_pb2

CONFIG = {}


@dataclass(frozen=True)
class GmailCredentials:
    secret: str
    token: str


@dataclass(frozen=True)
class GoogleCalendarCredentials:
    secret: str
    token: str


@dataclass(frozen=True)
class GithubCredentials:
    access_token: str


@dataclass(frozen=True)
class DiscordCredentials:
    access_token: str


@dataclass(frozen=True)
class SlackCredentials:
    access_token: str


@dataclass(frozen=True)
class TwitterCredentials:
    username: str
    password: str


@dataclass(frozen=True)
class TwilioCredentials:
    from_phone_number: str
    account_sid: str
    auth_token: str


def get_project_root() -> str:
    return CONFIG.get('npi_root', None) or os.environ.get('NPI_ROOT', None) or '/npiai'


def get_oai_key() -> str | None:
    return CONFIG.get('openai_api_key', None) or os.environ.get('OPENAI_API_KEY', None)


def get_gmail_credentials() -> GmailCredentials | None:
    return CONFIG.get(api_pb2.AppType.GOOGLE_GMAIL, None)


def set_gmail_credentials(secret: str, token: str):
    CONFIG[api_pb2.AppType.GOOGLE_GMAIL] = GmailCredentials(secret=secret, token=token)


def get_google_calendar_credentials() -> GoogleCalendarCredentials | None:
    return CONFIG.get(api_pb2.AppType.GOOGLE_CALENDAR, None)


def set_google_calendar_credentials(secret: str, token: str):
    CONFIG[api_pb2.AppType.GOOGLE_CALENDAR] = GoogleCalendarCredentials(secret=secret, token=token)


def set_github_credentials(access_token: str):
    CONFIG[api_pb2.AppType.GITHUB] = GithubCredentials(access_token=access_token)


def get_github_credentials() -> GithubCredentials | None:
    return CONFIG.get(api_pb2.AppType.GITHUB, None)


def set_discord_credentials(access_token: str):
    CONFIG[api_pb2.AppType.DISCORD] = DiscordCredentials(access_token=access_token)


def get_discord_credentials() -> DiscordCredentials | None:
    return CONFIG.get(api_pb2.AppType.DISCORD, None)


def set_twilio_credentials(account_sid: str, auth_token: str, from_phone_number: str):
    CONFIG[api_pb2.AppType.TWILIO] = TwilioCredentials(
        from_phone_number=from_phone_number,
        account_sid=account_sid,
        auth_token=auth_token)


def get_twilio_credentials() -> TwilioCredentials | None:
    return CONFIG.get(api_pb2.AppType.GITHUB.TWILIO, None)


def set_slack_credentials(access_token: str):
    CONFIG[api_pb2.AppType.SLACK] = SlackCredentials(access_token=access_token)


def get_slack_credentials() -> SlackCredentials | None:
    return CONFIG.get(api_pb2.AppType.SLACK, None)


def set_twitter_credentials(username: str, password: str):
    CONFIG[api_pb2.AppType.TWITTER] = TwitterCredentials(username=username, password=password)


def get_twitter_credentials() -> TwitterCredentials | None:
    return CONFIG.get(api_pb2.AppType.TWITTER, None)


def is_authorized(app: api_pb2.AppType) -> bool:
    return CONFIG.get(app, None) is not None

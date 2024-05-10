import os
from dataclasses import dataclass

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
    return CONFIG.get('gmail_credentials', None)


def set_gmail_credentials(secret: str, token: str):
    CONFIG['gmail_credentials'] = GmailCredentials(secret=secret, token=token)


def get_google_calendar_credentials() -> GoogleCalendarCredentials | None:
    return CONFIG.get('google_calendar_credentials', None)


def set_google_calendar_credentials(secret: str, token: str):
    CONFIG['google_calendar_credentials'] = GoogleCalendarCredentials(secret=secret, token=token)


def get_github_credentials() -> GithubCredentials | None:
    return CONFIG.get('github_credentials', None)


def get_twilio_credentials() -> TwilioCredentials | None:
    return CONFIG.get('twilio_credentials', None)


def set_github_credentials(access_token: str):
    CONFIG['github_credentials'] = GithubCredentials(access_token=access_token)


def get_discord_credentials() -> DiscordCredentials | None:
    return CONFIG.get('discord_credentials', None)


def set_discord_credentials(access_token: str):
    CONFIG['discord_credentials'] = DiscordCredentials(access_token=access_token)


def get_slack_credentials() -> SlackCredentials | None:
    return CONFIG.get('slack_credentials', None)


def set_slack_credentials(access_token: str):
    CONFIG['slack_credentials'] = SlackCredentials(access_token=access_token)


def get_twitter_credentials() -> TwitterCredentials | None:
    return CONFIG.get('twitter_credentials', None)


def set_twitter_credentials(username: str, password: str):
    CONFIG['twitter_credentials'] = TwitterCredentials(username=username, password=password)


def set_twilio_credentials(account_sid: str, auth_token: str, from_phone_number: str):
    CONFIG['twilio_credentials'] = TwilioCredentials(from_phone_number=from_phone_number,
                                                     account_sid=account_sid, auth_token=auth_token)

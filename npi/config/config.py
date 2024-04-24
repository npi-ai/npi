import os

CONFIG = {}


def get_project_root():
    return CONFIG.get('npi_root', os.environ.get('NPI_ROOT', '/npiai'))


def get_oai_key():
    return CONFIG.get('openai_api_key', os.environ.get('OPENAI_API_KEY', ''))


def get_gmail_credentials():
    if 'gmail_credentials' in CONFIG:
        return CONFIG['gmail_credentials']
    return None


def set_gmail_credentials(secret, token):
    CONFIG['gmail_credentials'] = {
        'secret': secret,
        'token': token
    }


def get_google_calendar_credentials():
    if 'google_calendar_credentials' in CONFIG:
        return CONFIG['google_calendar_credentials']
    return None


def set_google_calendar_credentials(secret, token):
    CONFIG['google_calendar_credentials'] = {
        'secret': secret,
        'token': token
    }

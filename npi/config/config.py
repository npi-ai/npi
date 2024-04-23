import os

CONFIG = {}


def get_project_root():
    return CONFIG.get('npi_root', os.environ.get('NPI_ROOT', '/npiai'))


def get_oai_key():
    return CONFIG.get('openai_api_key', os.environ.get('OPENAI_API_KEY', ''))


def create_credentials():
    cred_file = "/".join([get_project_root(), "config/credentials"])
    if not os.path.exists(cred_file):
        os.makedirs(cred_file)

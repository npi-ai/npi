import os
import json

CONFIG = {}


def get_project_root():
    try:
        if 'npi_root' in  CONFIG:
            return CONFIG["npi_root"]
        if os.environ["NPI_ROOT"]:
            return os.environ["NPI_ROOT"]
    except KeyError:
        pass
    return "/npiai"


def get_oai_key():
    try:
        if CONFIG["openai_api_key"]:
            return CONFIG["openai_api_key"]
        if os.environ["OPENAI_API_KEY"]:
            return os.environ["OPENAI_API_KEY"]
    except KeyError:
        pass
    return ""


def create_credentials():
    secrets = CONFIG["google_secret_key"]
    credentials_dir = "/".join([get_project_root(), "config/credentials"])
    if not os.path.exists("/".join([credentials_dir, "google.json"])):
        os.makedirs(credentials_dir)
        with open("/".join([credentials_dir, "google.json"]), "w") as f:
            f.write(secrets)

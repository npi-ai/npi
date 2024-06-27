import os
from npi.config import config


def test_init_discord_cred():
    config.set_discord_credentials(os.environ.get('DISCORD_ACCESS_TOKEN', None))

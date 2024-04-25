import os
from npi.config import config


def test_init_twitter_cred():
    config.set_twitter_credentials(
        username=os.environ.get('TWITTER_USERNAME', None),
        password=os.environ.get('TWITTER_PASSWORD', None),
    )

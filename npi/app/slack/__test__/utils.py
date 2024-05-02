import os
from npi.config import config


def test_init_slack_cred():
    config.set_slack_credentials(os.environ.get('SLACK_ACCESS_TOKEN', None))

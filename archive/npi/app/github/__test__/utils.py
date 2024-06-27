import os
from npi.config import config


def test_init_github_cred():
    config.set_github_credentials(os.environ.get('GITHUB_ACCESS_TOKEN', None))

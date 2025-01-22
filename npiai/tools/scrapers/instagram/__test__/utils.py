# SEE: https://subzeroid.github.io/instagrapi/usage-guide/best-practices.html
import os
import tempfile
from pathlib import Path

from instagrapi import Client
from instagrapi.exceptions import LoginRequired

from npiai.utils import logger

settings_file = Path(tempfile.gettempdir()) / "settings.json"

USERNAME = os.environ["INSTAGRAM_USERNAME"]
PASSWORD = os.environ["INSTAGRAM_PASSWORD"]


def login_user():
    """
    Attempts to login to Instagram using either the provided session information
    or the provided username and password.
    """

    client = Client(delay_range=[1, 3])
    session = None

    login_via_session = False
    login_via_pw = False

    if settings_file.exists():
        session = client.load_settings(settings_file)

    if session:
        try:
            client.set_settings(session)
            client.login(USERNAME, PASSWORD)

            # check if session is valid
            try:
                client.get_timeline_feed()
            except LoginRequired:
                logger.info(
                    "Session is invalid, need to login via username and password"
                )

                old_session = client.get_settings()

                # use the same device uuids across logins
                client.set_settings({})
                client.set_uuids(old_session["uuids"])

                client.login(USERNAME, PASSWORD)
            login_via_session = True
        except Exception as e:
            logger.info("Couldn't login user using session information: %s" % e)

    if not login_via_session:
        try:
            logger.info(
                "Attempting to login via username and password. username: %s" % USERNAME
            )
            if client.login(USERNAME, PASSWORD):
                login_via_pw = True
        except Exception as e:
            logger.info("Couldn't login user using username and password: %s" % e)

    if not login_via_pw and not login_via_session:
        raise Exception("Couldn't login user with either password or session")

    client.dump_settings(settings_file)
    logger.info("Logged in successfully")

    return client

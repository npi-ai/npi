import asyncio

from npi.app.slack import Slack
from utils import test_init_slack_cred


async def main():
    slack = Slack()
    res = await slack.chat(
        'Send a direct message to Dolphin (user id: "U071QBWBVCJ") asking if he is doing well, and wait for his reply.'
    )
    return res


if __name__ == '__main__':
    test_init_slack_cred()
    asyncio.run(main())

import os
import time
import base64
import threading

from openai import OpenAI

from npiai.core import Agent
from npiai.tools.hitl import ConsoleHandler
from npiai.app.discord import Discord
from npiai.browser_app.twitter import Twitter
from npiai.app.human_feedback import ConsoleFeedback

PROMPT = """
You are a Twitter Crawler capable of retrieving data from Twitter and sending messages to Discord.
The tools you can use are: Twitter, Discord, and Console Feedback.

## Rules

Here are some rules for you to fulfill the task:

1. The Twitter tool is a browser-based agent that can simulate human interactions on twitter. You should pass a detailed subtask to it.
2. If the discord channel ID is not provided, you should ask the user for it.
3. If you need confirmation from the user to complete the task, or you want to ask the user a question, you can use the Console Feedback tool to do so. Especially, if the last assistant's message proposed a question, you should ask the user for response.

## Example
Task: Get the last tweet from @npi_ai and send it to Discord.
Steps:
1. twitter("Get the last tweet from @npi_ai")
2. console_feedback("Which channel would you like to send the message to? Please specify the channel ID.")
3. discord("Send the message {{message}} to channel with ID: {{channel_id}}.")
"""


def main():
    crawler = Agent(
        agent_name='twitter_crawler',
        description='Retrieve data from Twitter and send messages to Discord',
        prompt=PROMPT,
        llm=OpenAI(),
        hitl_handler=ConsoleHandler(),
    )

    twitter = Twitter(
        username=os.environ['TWITTER_USERNAME'],
        password=os.environ['TWITTER_PASSWORD'],
    )

    crawler.use(
        twitter,
        Discord(access_token=os.environ['DISCORD_ACCESS_TOKEN']),
        ConsoleFeedback(),
    )

    crawler.authorize()

    running = True

    def save_screenshot():
        if os.path.exists('./screenshots'):
            os.rmdir('./screenshots')
        os.makedirs('./screenshots', exist_ok=True)
        count = 0

        while running:
            screenshot = twitter.screenshot()
            if screenshot:
                with open(f'./screenshots/{count}.png', 'wb') as f:
                    f.write(base64.b64decode(screenshot.split(',')[1]))
                count += 1
            time.sleep(1)

    print('Twitter Crawler: What\'s your task for me?')
    task = input('User: ')
    print('')
    thread = threading.Thread(target=save_screenshot)
    thread.start()
    crawler.run(task)
    running = False


if __name__ == "__main__":
    main()

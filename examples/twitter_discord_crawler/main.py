import asyncio
import os

from npiai import FunctionTool, agent_wrapper
from npiai.hitl_handler import ConsoleHandler
from npiai.tools import Discord
from npiai.tools.browser import Twitter
from npiai import OpenAI

PROMPT = """
You are a Twitter Crawler capable of retrieving data from Twitter and sending messages to Discord.
The tools you can use are: Twitter, Discord, and Console Feedback.

## Rules

Here are some rules for you to fulfill the task:

1. The Twitter tool is a chrome-based agent that can simulate human interactions on twitter. You should pass a detailed subtask to it.
2. If the discord channel ID is not provided, you should ask the user for it.
3. If you need confirmation from the user to complete the task, or you want to ask the user a question, you can use the Console Feedback tool to do so. Especially, if the last assistant's message proposed a question, you should ask the user for response.

## Example
Task: Get the last tweet from @npi_ai and send it to Discord.
Steps:
1. Chat with the twitter tools: "Get the last tweet from @npi_ai"
2. Ask human for additional information: "Which channel would you like to send the message to? Please specify the channel ID."
3. Chat with the discord tools: "Send the message {{message}} to channel with ID: {{channel_id}}."
"""


class TwitterDiscordCrawler(FunctionTool):
    def __init__(self):
        super().__init__(
            name='twitter_crawler',
            description='Retrieve data from Twitter and send messages to Discord',
            system_prompt=PROMPT,
        )

        self.use_hitl(ConsoleHandler())

        self.add_tool(
            agent_wrapper(Twitter(headless=False)),
            agent_wrapper(Discord()),
        )


async def run():
    llm = OpenAI(model='gpt-4-turbo-preview', api_key=os.environ['OPENAI_API_KEY'])

    async with agent_wrapper(TwitterDiscordCrawler(), llm=llm) as agent:
        print("Twitter Crawler: What's your task for me?")
        task = input('User: ')
        print('')
        await agent.chat(task)


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()

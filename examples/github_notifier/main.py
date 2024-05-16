import os

from openai import OpenAI
from npiai.core import Agent
from npiai.tools.hitl.console import ConsoleHandler
from npiai.app.github import GitHub
from npiai.app.google import Gmail


def main():
    agent = Agent(
        agent_name='github_notifier',
        prompt='You are a Github Notifier that informs users when a new issue or pull request is open.',
        description='Github Notifier that informs users when a new issue or pull request is open',
        llm=OpenAI(),
        hitl_handler=ConsoleHandler()
    )

    with open('./credentials.json') as f:
        google_creds = f.read()

    agent.use(
        GitHub(access_token=os.environ['GITHUB_ACCESS_TOKEN']),
        Gmail(
            secret=google_creds,
            # TODO: redirect uri
            redirect_uri='',
        )
    )

    agent.authorize()

    task = 'idiotWu/npi-test has a new issue, send an email to daofeng@npi.ai with the body of issue'

    print(f'[GitHub Notifier] Task: {task}')

    agent.when(task)


if __name__ == '__main__':
    main()

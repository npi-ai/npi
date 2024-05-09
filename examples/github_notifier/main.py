from openai import OpenAI
from npiai.core import Agent
from npiai.app.github import GitHub
from npiai.app.google import Gmail
from npiai.app.human_feedback import ConsoleFeedback


def main():
    agent = Agent(
        agent_name='github_notifier',
        prompt='You are a Github Notifier that informs users when a new issue or pull request is open.',
        description='Github Notifier that informs users when a new issue or pull request is open',
        llm=OpenAI()
    )
    agent.use(GitHub(), Gmail(), ConsoleFeedback())

    agent.when("idiotWu/npi-test has a new issue, send an email to daofeng@npi.ai with the body of issue")


if __name__ == '__main__':
    main()

from openai import OpenAI
from npiai.deprecated.core import Agent
from npiai.deprecated.app import GitHub
from npiai.deprecated.app.google import Gmail


def main():
    agent = Agent(
        agent_name='github_notifier',
        prompt="You are a Github Agent",
        description='Github Agent',
        llm=OpenAI()
    )
    agent.use(GitHub(), Gmail())

    agent.when("idiotWu/npi-test has a new issue, send an email to daofeng@npi.ai with the body of issue")


if __name__ == '__main__':
    main()

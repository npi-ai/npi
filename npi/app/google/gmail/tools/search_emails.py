from pydantic import Field
from npi.app.google.gmail.shared import Agent, Parameter, gmail_agent, gmail_client
from typing import Optional
import json


class SearchEmailsParameter(Parameter):
    query: Optional[str] = Field(default=None, description='A Gmail query to match emails')
    max_results: int = Field(default=100, description='Maximum number of messages to return')


def search_emails(_agent: Agent, params: SearchEmailsParameter):
    print('Retrieving messages: ', json.dumps(params.dict(), indent=2))

    return gmail_client.get_messages(
        query=params.query,
        max_results=params.max_results,
    )


gmail_agent.register(
    fn=search_emails,
    description='Search for emails with a query',
    Params=SearchEmailsParameter,
)

if __name__ == '__main__':
    msgs = gmail_agent.chat(
        'Find the latest email from daofeng.wu@emory.edu'
    )

    print(msgs)

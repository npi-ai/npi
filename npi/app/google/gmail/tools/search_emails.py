from pydantic import Field
from npi.app.google.gmail.shared import Parameter, FunctionRegistration, GmailAgent
from typing import Optional
import json


class SearchEmailsParameter(Parameter):
    query: Optional[str] = Field(default=None, description='A Gmail query to match emails')
    max_results: int = Field(default=100, description='Maximum number of messages to return')


def search_emails(params: SearchEmailsParameter, agent: GmailAgent, _prompt: str):
    print('Retrieving messages: ', json.dumps(params.dict(), indent=2))

    return agent.gmail_client.get_messages(
        query=params.query,
        max_results=params.max_results,
    )


search_emails_registration = FunctionRegistration(
    fn=search_emails,
    description='Search for emails with a query',
    Params=SearchEmailsParameter,
)

if __name__ == '__main__':
    from npi.app.google.gmail.tools import gmail_functions

    gmail_agent = GmailAgent(function_list=gmail_functions)

    msgs = gmail_agent.chat(
        'Find the latest email from daofeng.wu@emory.edu'
    )

    print(msgs)

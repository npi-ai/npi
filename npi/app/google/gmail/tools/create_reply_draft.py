from pydantic import Field
from markdown import markdown
from npi.app.google.gmail.shared import Parameter, FunctionRegistration, GmailAgent, confirm
from typing import Optional
import json
import re
import html

pattern = re.compile(r'```.*\n([\s\S]+)```')


class CreateReplyDraftParameter(Parameter):
    query: Optional[str] = Field(default=None, description='A Gmail query to match emails')
    max_results: int = Field(default=100, description='Maximum number of messages to return')


def _generate_reply(agent: GmailAgent, content: str, prompt: str) -> str:
    response = agent.client.chat.completions.create(
        model=agent.model,
        messages=[{
            'role': 'system',
            'content': """
You are an assistant helping user to reply emails in markdown format. For example:

User: Ping
You: Pong"""
        }, {
            'role': 'user',
            'content': prompt
        }, {
            'role': 'user',
            'content': 'Email body:\n' + content
        }]
    )

    content = response.choices[0].message.content
    match = pattern.search(content)

    return markdown(match.groups()[0] if match else content)


def create_reply_draft(params: CreateReplyDraftParameter, agent: GmailAgent, prompt: str):
    print('Retrieving messages: ', json.dumps(params.dict(), indent=2))

    messages = agent.gmail_client.get_messages(
        query=params.query,
        max_results=params.max_results,
    )

    print(f'Retrieved {len(messages)} messages(s):', messages)

    for msg in messages:
        content = msg.plain or msg.html
        res = _generate_reply(agent, content, prompt)

        if confirm(f'Create a draft to email:\n{content}\nwith:\n{res}'):
            print('Creating draft...')
            agent.gmail_client.create_draft(
                sender='',
                to=msg.sender,
                cc=msg.cc,
                bcc=msg.bcc,
                subject='Re: ' + msg.subject,
                # TODO: email template
                msg_html=res + f'<div>On {msg.date} {html.escape(msg.sender)} wrote:<br> <blockquote>{msg.html}</blockquote></div>',
                reply_to=msg,
            )


create_reply_draft_registration = FunctionRegistration(
    fn=create_reply_draft,
    description='Create a reply draft to emails matching the search query',
    Params=CreateReplyDraftParameter,
)

if __name__ == '__main__':
    from npi.app.google.gmail.tools import gmail_functions

    gmail_agent = GmailAgent(function_list=gmail_functions)

    gmail_agent.chat(
        'Create a reply draft to the latest email from daofeng.wu@emory.edu'
    )

from pydantic import Field
from markdown import markdown
from npi.app.google.gmail.shared import Agent, Parameter, gmail_agent, gmail_client, confirm
from typing import Optional
import json
import re
import html

pattern = re.compile(r'```.*\n([\s\S]+)```')


class CreateReplyDraftParameter(Parameter):
    query: Optional[str] = Field(default=None, description='A Gmail query to match emails')
    max_results: int = Field(default=100, description='Maximum number of messages to return')


def _generate_reply(agent: Agent, content: str) -> str:
    response = agent.client.chat.completions.create(
        model=agent.model,
        messages=[{
            'role': 'system',
            'content': """
You are an assistant helping user to reply emails. For example:

User: Ping
You: Pong"""
        }, {
            'role': 'user',
            'content': content
        }]
    )

    content = response.choices[0].message.content
    match = pattern.search(content)

    return markdown(match.groups()[0] if match else content)


def create_reply_draft(agent: Agent, params: CreateReplyDraftParameter):
    print('Retrieving messages: ', json.dumps(params.dict(), indent=2))

    messages = gmail_client.get_messages(
        query=params.query,
        max_results=params.max_results,
    )

    print(f'Retrieved {len(messages)} messages(s):', messages)

    for msg in messages:
        content = msg.plain or msg.html
        res = _generate_reply(agent, content)

        if confirm(f'Create a draft to email:\n{content}\nwith:\n{res}'):
            print('Creating draft...')
            gmail_client.create_draft(
                sender='',
                to=msg.sender,
                cc=msg.cc,
                bcc=msg.bcc,
                subject='Re: ' + msg.subject,
                # TODO: email template
                msg_html=res + f'<div>On {msg.date} {html.escape(msg.sender)} wrote:<br> <blockquote>{msg.html}</blockquote></div>',
                reply_to=msg,
            )


gmail_agent.register(
    fn=create_reply_draft,
    description='Create a reply draft to emails matching the search query',
    Params=CreateReplyDraftParameter,
)

if __name__ == '__main__':
    gmail_agent.chat(
        'Create a reply draft to the latest email from daofeng.wu@emory.edu'
    )

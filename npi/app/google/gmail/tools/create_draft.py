from pydantic import Field
from typing import List, Optional
from npi.app.google.gmail.shared import FunctionRegistration, Parameter, GmailAgent, confirm
from markdown import markdown


class CreateDraftParameter(Parameter):
    to: str = Field(description='The email address the message is being sent to')
    subject: str = Field(description='The subject line of the email')
    message: Optional[str] = Field(default=None, description='The email content in markdown format')
    cc: Optional[List[str]] = Field(default=None, description='The list of email addresses to be cc\'d')
    bcc: Optional[List[str]] = Field(default=None, description='The list of email addresses to be bcc\'d')


def create_draft(params: CreateDraftParameter, agent: GmailAgent, _prompt: str):
    if confirm('Create draft', params):
        print('Creating draft...')
        agent.gmail_client.create_draft(
            sender='',
            to=params.to,
            cc=params.cc,
            bcc=params.bcc,
            subject=params.subject,
            msg_html=markdown(params.message),
        )


create_draft_registration = FunctionRegistration(
    fn=create_draft,
    description='Create and insert a draft email',
    Params=CreateDraftParameter,
)

if __name__ == '__main__':
    from npi.app.google.gmail.tools import gmail_functions

    gmail_agent = GmailAgent(function_list=gmail_functions)

    gmail_agent.chat(
        'Create a draft email to dolphin.w.e+test@gmail.com stating that the email is sent from the NPi Gmail Agent. You should test markdown features in the email body. Also CC dolphin.w.e+cc@gmail.com'
    )

from pydantic import Field
from typing import List, Optional
from npi.app.google.gmail.shared import Agent, Parameter, gmail_agent, gmail_client, confirm
from markdown import markdown


class SendEmailParameter(Parameter):
    to: str = Field(description='The email address the message is being sent to')
    subject: str = Field(description='The subject line of the email')
    message: Optional[str] = Field(default=None, description='The email content in markdown format')
    cc: Optional[List[str]] = Field(default=None, description='The list of email addresses to be cc\'d')
    bcc: Optional[List[str]] = Field(default=None, description='The list of email addresses to be bcc\'d')


def send_email(params: SendEmailParameter, _prompt: str, _agent: Agent):
    if confirm('Sending an email', params):
        print('Sending email...')
        gmail_client.send_message(
            sender='',
            to=params.to,
            cc=params.cc,
            bcc=params.bcc,
            subject=params.subject,
            msg_html=markdown(params.message),
        )


gmail_agent.register(
    fn=send_email,
    description='Send an email using gmail',
    Params=SendEmailParameter,
)

if __name__ == '__main__':
    gmail_agent.chat(
        'Send a test email to dolphin.w.e+test@gmail.com stating that the email is sent from the NPi Gmail Agent. You should test markdown features in the email body. Also CC dolphin.w.e+cc@gmail.com'
    )

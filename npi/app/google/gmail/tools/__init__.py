from npi.app.google.gmail.shared.function_registration import FunctionRegistration
from npi.app.google.gmail.tools.add_labels import add_labels_registration
from npi.app.google.gmail.tools.create_draft import create_draft_registration
from npi.app.google.gmail.tools.create_reply_draft import create_reply_draft_registration
from npi.app.google.gmail.tools.remove_labels import remove_labels_registration
from npi.app.google.gmail.tools.reply import reply_registration
# from npi.app.google.gmail.tools.search_emails import search_emails_registration
from npi.app.google.gmail.tools.send_email import send_email_registration
from typing import List

gmail_functions: List[FunctionRegistration] = [
    add_labels_registration,
    create_draft_registration,
    create_reply_draft_registration,
    remove_labels_registration,
    reply_registration,
    # search_emails_registration,
    send_email_registration,
]

__all__ = [
    'add_labels_registration',
    'create_draft_registration',
    'create_reply_draft_registration',
    'remove_labels_registration',
    'reply_registration',
    # 'search_emails_registration',
    'send_email_registration',
    'gmail_functions',
]

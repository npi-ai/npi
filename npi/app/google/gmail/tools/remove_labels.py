from pydantic import Field
from typing import List, Optional
from npi.app.google.gmail.shared import Parameter, FunctionRegistration, GmailAgent, confirm
import json


class RemoveLabelsParameter(Parameter):
    query: Optional[str] = Field(default=None, description='A Gmail query to match emails')
    max_results: int = Field(default=100, description='Maximum number of messages to return')
    labels: List[str] = Field(description='A list of labels to remove')


def remove_labels(params: RemoveLabelsParameter, agent: GmailAgent, _prompt: str):
    print('Retrieving messages: ', json.dumps(params.dict(), indent=2))

    emails = agent.gmail_client.get_messages(
        query=params.query,
        max_results=params.max_results,
    )

    print(f'Retrieved {len(emails)} message(s)')

    if len(emails) == 0:
        print('No email matches query')
        return

    print('Retrieving current labels...')
    labels = agent.gmail_client.list_labels()
    label_name_map = {label.name: label for label in labels}
    labels_to_remove = []
    print(labels)

    for lbl in params.labels:
        if lbl in label_name_map:
            labels_to_remove.append(label_name_map[lbl])

    if len(labels_to_remove) == 0:
        print('No label to remove')
        return

    for msg in emails:
        print('Email:', msg)
        if confirm(f'Remove label(s): {labels_to_remove}'):
            agent.gmail_client.remove_labels(msg, labels_to_remove)


remove_labels_registration = FunctionRegistration(
    fn=remove_labels,
    description='Remove labels from the emails matching the search query',
    Params=RemoveLabelsParameter,
)

if __name__ == '__main__':
    from npi.app.google.gmail.tools import gmail_functions

    gmail_agent = GmailAgent(function_list=gmail_functions)

    gmail_agent.chat(
        'Remove label "TEST" from the latest email from daofeng.wu@emory.edu'
    )

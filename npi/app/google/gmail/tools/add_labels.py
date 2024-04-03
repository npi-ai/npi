from pydantic import Field
from typing import List, Optional
from npi.app.google.gmail.shared import Agent, Parameter, gmail_agent, gmail_client, confirm
import json


class AddLabelsParameter(Parameter):
    query: Optional[str] = Field(default=None, description='A Gmail query to match emails')
    max_results: int = Field(default=100, description='Maximum number of messages to return')
    labels: List[str] = Field(description='A list of labels to add')


def add_labels(params: AddLabelsParameter, _prompt: str, _agent: Agent):
    print('Retrieving messages: ', json.dumps(params.dict(), indent=2))

    emails = gmail_client.get_messages(
        query=params.query,
        max_results=params.max_results,
    )

    print(f'Retrieved {len(emails)} message(s)')

    if len(emails) == 0:
        print('No email matches query')
        return

    print('Retrieving current labels...')
    labels = gmail_client.list_labels()
    label_name_map = {label.name: label for label in labels}
    labels_to_add = []
    print(labels)

    for lbl in params.labels:
        if lbl not in label_name_map and confirm(f'Creating new label: {lbl}'):
            new_label = gmail_client.create_label(lbl)
            label_name_map[lbl] = new_label
        labels_to_add.append(label_name_map[lbl])

    for msg in emails:
        print('Email:', msg)

        if confirm(f'Add label(s): {labels_to_add}'):
            gmail_client.add_labels(msg, labels_to_add)


gmail_agent.register(
    fn=add_labels,
    description='Add labels to the emails matching the search query',
    Params=AddLabelsParameter,
)

if __name__ == '__main__':
    gmail_agent.chat(
        'Add label "TEST" to the latest email from daofeng.wu@emory.edu'
    )

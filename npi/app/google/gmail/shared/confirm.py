from npi.app.google.gmail.shared.parameter import Parameter
import json


def confirm(message: str, params: Parameter = None) -> bool:
    print(message)

    if params:
        print(json.dumps(params.dict(), indent=2))

    should_run = input('Confirm? [y/N]: ').lower() == 'y'

    if not should_run:
        print('Action cancelled')

    return should_run

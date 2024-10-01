import json
import re


def parse_json_response(response: str):
    try:
        match = re.match(r"```.*\n([\s\S]+)```", response)
        data = json.loads(match.group(1)) if match else json.loads(response)
        return data
    except json.JSONDecodeError:
        return None

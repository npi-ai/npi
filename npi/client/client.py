"""Client for the NPI"""


class NPiClient:
    """Client for the NPI"""
    openai_key: str

    def __init__(self, openai_key):
        self.openai_key = openai_key

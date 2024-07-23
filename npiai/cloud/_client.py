import requests


class Client:

    def __init__(self, api_key='', base_url='https://api.npi.ai'):
        self.api_key = api_key
        self.base_url = base_url
        self.client = requests.Session()
        self.client.headers.update({'Content-Type': 'application/json'})
        self.client.headers.update({'Accept': 'application/json'})

    def get_credentials(self, permission_name: str):
        return self.api_key

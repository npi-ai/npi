from pydantic import Field
from npi.types import Parameters


class GetTweetsParameters(Parameters):
    max_results: int = Field(default=-1, description='Maximum number of tweets to return. Pass -1 for no limit.')


class OpenTweetParameters(Parameters):
    url: str = Field(description='URL of the tweet you want to open.')

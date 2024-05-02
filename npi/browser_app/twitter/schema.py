from typing import Literal
from pydantic import Field
from npi.types import Parameters


class GetTweetsParameters(Parameters):
    max_results: int = Field(default=-1, description='Maximum number of tweets to return. Pass -1 for no limit.')


class OpenTweetParameters(Parameters):
    url: str = Field(description='URL of the tweet you want to open.')


class SearchParameters(Parameters):
    query: str = Field(description='Twitter search query')
    sort_by: Literal['hottest', 'latest'] = Field(
        default='hottest', description='Sort results by this parameter. Default is "hottest"'
    )


class GotoProfileParameters(Parameters):
    username: str = Field(description='Twitter username')


class ReplyParameters(Parameters):
    url: str = Field(description='URL of the tweet you want to reply')
    content: str = Field(description='Reply content')

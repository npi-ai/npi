from enum import Enum
from typing import List, Union
import os
import asyncio
from litellm import acompletion, ModelResponse, CustomStreamWrapper, drop_params


class Provider(Enum):
    OpenAI = 1
    Llama = 2
    Anthropic = 3
    Groq = 4
    AzureOpenAI = 5
    Gemini = 6


class LLM:
    def __init__(self, api_key: str, model: str, provider: Provider):
        self.model = model
        self.api_key = api_key
        self.provider = provider

    def default_model(self) -> str:
        return self.model

    def get_provider(self) -> Provider:
        return self.provider

    # TODO: kwargs typings
    async def completion(self, **kwargs) -> Union[ModelResponse, CustomStreamWrapper]:
        return await acompletion(
            model=self.model, api_key=self.api_key, drop_params=True, **kwargs
        )

    def completion_sync(self, **kwargs) -> Union[ModelResponse, CustomStreamWrapper]:
        return asyncio.run(self.completion(**kwargs))


class OpenAI(LLM):
    def __init__(self, api_key: str, model: str):
        super().__init__(api_key=api_key, model=model, provider=Provider.OpenAI)


class Anthropic(LLM):
    def __init__(self, api_key: str, model: str):
        super().__init__(
            api_key=api_key, model=f"anthropic/{model}", provider=Provider.Anthropic
        )


class AzureOpenAI(LLM):
    def __init__(
        self, api_key: str, api_base: str, api_version: str, deployment_name: str
    ):
        os.environ["AZURE_API_BASE"] = api_base
        os.environ["AZURE_API_VERSION"] = api_version
        super().__init__(f"azure/{deployment_name}", api_key, Provider.AzureOpenAI)


class Gemini(LLM):
    def __init__(self, api_key: str, model: str):
        super().__init__(
            api_key=api_key, model=f"gemini/{model}", provider=Provider.Gemini
        )

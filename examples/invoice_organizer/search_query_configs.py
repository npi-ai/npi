import json
from textwrap import dedent
from typing import Dict, Any

from pydantic import BaseModel, Field, create_model
from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from npiai import Configurator, Context
from npiai.types import FunctionRegistration
from npiai.utils import sanitize_schema

from constants import StorageKeys


class SearchQueryConfigsModel(BaseModel):
    keywords: str | None = Field(
        default=None, description="Keywords or phrases to search for"
    )
    sender: str | None = Field(default=None, description="Sender email")
    recipient: str | None = Field(default=None, description="Recipient email")
    subject: str | None = Field(default=None, description="Words in the subject line")
    label: str | None = Field(
        default=None, description="The label that the email should have"
    )
    start_date: str | None = Field(
        default=None, description="The start date for the search query"
    )
    end_date: str | None = Field(
        default=None, description="The end date for the search query"
    )
    in_folder: str | None = Field(
        default="inbox", description="The folder containing the target emails"
    )
    has_pdf_attachments: bool | None = Field(
        default=False, description="Does the email have PDF attachments?"
    )


class SearchQueryConfigs(Configurator):
    model = SearchQueryConfigsModel
    storage_key = StorageKeys.QUERY

    name = "search_query_builder"

    description = dedent(
        """
        Build Gmail search query based on the search criteria. For example, 
        to search for emails from someone@example.com, you may invoke this agent with 
        `chat(instruction="search for emails sent by someone@example.com")`
        """
    )

    system_prompt = dedent(
        """
        You are an agent helping user compose a Gmail search query by interpreting 
        natural language instructions. For any given instruction, you must:
        
            1. Identify and extract key search criteria from the user's instruction, 
               including `keywords`, `sender`, and any other pertinent details.
            2. Engage with the `compose_configs` tool, inputting identified criteria and 
               leaving unspecified fields as `None`. The tool will interact with the 
               user to define any missing information, so you should always call this
               tool even if no criteria are present.
           
        ## Examples
        
        Instruction: search for emails sent by someone@example.com in the last week
        Steps:
            a. Extracted criteria: `sender="someone@example.com"`.
            b. Interaction with `compose_configs`: `compose_configs(sender="someone@example.com", start_date="last week")`
            
        Instruction: search for github emails from 2024/7/1 to yesterday
        Steps:
            a. Extracted criteria: `keywords="github", start_data="2024/7/1", end_date="yesterday"`.
            b. Interaction with `compose_configs`: 
               `compose_configs(keywords="github", start_data="2024/7/1", end_date="yesterday")`
        """
    )

    async def save_configs(self, ctx: Context, **composed_configs: Dict[str, Any]):
        criteria = {}

        # remove empty fields
        for k, v in composed_configs.items():
            if v is not None and v != "":
                criteria[k] = composed_configs[k]

        model = create_model(
            "save_query_model",
            query=(
                str,
                "Gmail search query",
            ),
        )

        fn_reg = FunctionRegistration(
            fn=self.save_query,
            name="save_query",
            ctx_variables=[],
            ctx_param_name="ctx",
            description="Save the query into context storage",
            model=model,
            schema=sanitize_schema(model),
        )

        messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=dedent(
                    """
                    Transform the given criteria into a Gmail search query with steps below:
                    
                    1. Identify and extract key search criteria from the given JSON object, 
                       including `keywords`, `sender`, and any other pertinent details.
                    2. Formulate a Gmail search query using the criteria.
                    3. Utilize the `save_query` tool to record the search query.
                    
                    ## How to construct a Gmail search query
        
                    - Keywords: separate them with space
                    - Sender: use `from:<sender>` filter
                    - Recipient: use `to:<recipient>` filter
                    - Subject: use `subject:<subject>` filter
                    - Label: use `label:<label>` filter. There should be no space in label
                    - Start date: use `after:<date>` filter if it is an absolute date. Otherwise,
                      convert the date to ~d (day), ~m (month), or ~y (year) format, and use
                      `newer_than:<relative_start_date>` filter.
                    - End date: use `before:<date>` filter if it is an absolute date. Otherwise,
                      convert the date to relative format and use `older_than:<relative_end_date>`
                      filter.
                    - Folder: use `in:<folder>` filter
                    - PDF attachments: use `filename:*.pdf` filter if the emails have pdf attachments
                    
                    ## Examples
        
                    Input: {"sender": "someone@example.com", "start_date": "last week"}
                    Steps:
                        a. Formulate the Gmail search query using the criteria: 
                           `from:someone@example.com newer_than:7d daily`.
                        b. Record the query: `save_query(query="from:someone@example.com newer_than:7d")`.
                        
                    Input: {"keywords": "github", "start_date": "2024/7/1", "end_date": "yesterday", "has_pdf_attachment": true}
                    Steps:
                        a. Formulate the Gmail search query using the criteria: 
                           `after:2024/7/1 older_than:1d github`.
                        b. Record the query: `save_query(query="after:2024/7/1 older_than:1d filename:*.pdf github")`.
                    """
                ),
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=json.dumps(criteria),
            ),
        ]

        response = await ctx.llm.completion(
            messages=messages,
            tools=[fn_reg.get_tool_param()],
            tool_choice="required",
            max_tokens=4096,
        )

        response_message = response.choices[0].message
        tool_calls = response_message.get("tool_calls", None)

        if not tool_calls:
            raise RuntimeError("No tool call received to save query")

        args = json.loads(tool_calls[0].function.arguments)

        await ctx.send_debug_message(f"[{self.name}] Received {args}")

        await self.save_query(ctx, **args)

    async def save_query(self, ctx: Context, query: str):
        """
        Save the query into context storage.

        Args:
            ctx: NPi Context object.
            query: Gmail search query.
        """
        confirmed = await ctx.hitl.confirm(
            tool_name=self.name,
            message=f"Does the search query `{query}` look good to you?",
        )

        if not confirmed:
            query = await ctx.hitl.input(
                tool_name=self.name,
                message=f"Amend the search query",
                default=query,
            )

        await ctx.kv.save(StorageKeys.QUERY, query)


if __name__ == "__main__":
    import asyncio
    from npiai.hitl_handler import ConsoleHandler

    from debug_context import DebugContext

    async def main():
        ctx = DebugContext()
        ctx.use_hitl(ConsoleHandler())
        ctx.use_configs(SearchQueryConfigs())

        await ctx.setup_configs("search for emails containing invoice")

        print("query:", await ctx.kv.get(StorageKeys.QUERY))

    asyncio.run(main())

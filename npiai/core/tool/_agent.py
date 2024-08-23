import json
import uuid
from textwrap import dedent
from typing import List, Any, Dict, Literal, get_origin, get_args, Type
from pydantic import create_model, Field, BaseModel

from npiai.types import FunctionRegistration
from npiai.context import Context, Task
from npiai.core.base import BaseAgentTool
from npiai.core.tool._function import FunctionTool
from npiai.core.tool._browser import BrowserTool
from npiai.utils import sanitize_schema, get_type_annotation

from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)


class AgentTool(BaseAgentTool):
    _tool: FunctionTool
    _config_agents: List["ConfigAgentTool"]

    def __init__(self, tool: FunctionTool):
        super().__init__()
        self.name = f"{tool.name}_agent"
        self._tool = tool
        self._config_agents = []
        self.description = tool.description
        self.provider = tool.provider

    def use_configs(self, *config_agents: "ConfigAgentTool"):
        self._config_agents.extend(config_agents)

    def unpack_functions(self) -> List[FunctionRegistration]:
        # Wrap the chat function of this agent to FunctionRegistration
        model = create_model(
            f"{self.name}_agent_model",
            instruction=(
                str,
                Field(
                    description=f"The task you want {self._tool.name} to do or "
                    f"the message you want to chat with {self._tool.name}"
                ),
            ),
        )

        fn_reg = FunctionRegistration(
            fn=self.chat,
            name="chat",
            ctx_variables=[],
            ctx_param_name="ctx",
            description=f"This is an api of an AI Assistant, named {self.name}, the abilities of the assistant is:\n "
            f"{self.description}\n"
            f"You can use this function to direct the assistant to accomplish task for you.",
            model=model,
            schema=sanitize_schema(model),
        )

        return [fn_reg]

    async def start(self):
        await self._tool.start()

    async def end(self):
        await self._tool.end()

    async def setup_configs(self, ctx: Context, instruction: str):
        for config_agent in self._config_agents:
            await config_agent.chat(ctx, instruction)

    async def chat(
        self,
        ctx: Context,
        instruction: str,
    ) -> str:
        await self.setup_configs(ctx, instruction)

        task = Task(goal=instruction)
        ctx.with_task(task)
        if self._tool.system_prompt:
            await task.step(
                [
                    ChatCompletionSystemMessageParam(
                        role="system", content=self._tool.system_prompt
                    )
                ]
            )

        await task.step(
            [ChatCompletionUserMessageParam(role="user", content=instruction)]
        )
        return await self._call_llm(ctx, task)

    async def _call_llm(self, ctx: Context, task: Task) -> str:
        while True:
            response = await ctx.llm.completion(
                messages=task.conversations(),
                tools=self._tool.tools,
                tool_choice="auto",
                max_tokens=4096,
            )
            await task.step([response.choices[0].message])

            response_message = response.choices[0].message
            tool_calls = response_message.get("tool_calls", None)

            if tool_calls is None:
                return response_message.content

            results = await self._tool.call(tool_calls, ctx)
            await task.step(results)


class BrowserAgentTool(AgentTool):
    _tool: BrowserTool

    def __init__(self, tool: BrowserTool):
        super().__init__(tool)

    async def get_screenshot(self) -> str | None:
        return await self._tool.get_screenshot()

    async def goto_blank(self):
        await self._tool.goto_blank()

    async def chat(
        self,
        ctx: Context,
        instruction: str,
    ) -> str:
        if not self._tool.use_screenshot:
            return await super().chat(ctx, instruction)

        screenshot = await self._tool.get_screenshot()

        if not screenshot:
            return await super().chat(ctx, instruction)

        await self.setup_configs(ctx, instruction)

        task = Task(goal=instruction)
        ctx = ctx.fork(task)
        if self._tool.system_prompt:
            await task.step(
                [
                    ChatCompletionSystemMessageParam(
                        role="system", content=self._tool.system_prompt
                    )
                ]
            )

        await task.step(
            [
                ChatCompletionUserMessageParam(
                    role="user",
                    content=[
                        {
                            "type": "text",
                            "text": instruction,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": screenshot,
                            },
                        },
                    ],
                )
            ]
        )

        return await self._call_llm(ctx, task)


class ConfigAgentTool(BaseAgentTool):
    model: Type[BaseModel]
    storage_key: str = str(uuid.uuid4())

    name = "config_agent"
    description = "Set up user preferences based on natural language instructions"
    system_prompt = dedent(
        """
        You are an agent helping user set up config fields by interpreting natural 
        language instructions. For any given instruction, you must:
        
            1. Identify and extract key criteria from the user's instruction.
            2. Engage with the `compose_configs` tool, inputting identified criteria and 
               leaving unspecified fields as `None`. The tool will interact with the 
               user to define any missing information, so you should always call this
               tool even if no criteria are present.
        """
    )

    async def start(self):
        pass

    async def end(self):
        pass

    def unpack_functions(self) -> List[FunctionRegistration]:
        model = create_model(
            f"{self.name}_config_agent_model",
            instruction=(
                str,
                Field(
                    description="Natural language instruction for setting up user preferences"
                ),
            ),
        )

        fn_reg = FunctionRegistration(
            fn=self.chat,
            name="chat",
            ctx_variables=[],
            ctx_param_name="ctx",
            description=self.description,
            model=model,
            schema=sanitize_schema(model),
        )

        return [fn_reg]

    async def chat(self, ctx: Context, instruction: str) -> str:
        await ctx.send_debug_message(f"[{self.name}] Setting up config fields")

        current_configs = await ctx.kv.get(
            key=self.storage_key,
            ask_human=False,
        )

        if not current_configs:
            composed_configs = await self._parse_instruction(ctx, instruction)
            await self._finalize_configs(ctx, composed_configs)
        else:
            await ctx.send_debug_message(f"Use existing configs: {current_configs}")

        return "Configs saved"

    async def save_configs(self, ctx: Context, **composed_configs: Dict[str, Any]):
        await ctx.kv.save(self.storage_key, json.dumps(composed_configs))

    async def delete_configs(self, ctx: Context):
        await ctx.kv.delete(self.storage_key)

    async def compose_configs(self, ctx: Context, **parsed_configs: Dict[str, Any]):
        results = {}

        for key, field in self.model.model_fields.items():
            default_value = parsed_configs.get(key, None)

            if default_value is None and not field.is_required():
                default_value = field.default

            annotation = get_type_annotation(field.annotation)
            typing = get_origin(annotation) or annotation
            field_description = (field.description or key).lower()

            if typing is bool:
                response = await ctx.hitl.confirm(
                    tool_name=self.name,
                    message=field_description,
                    default=default_value or False,
                )
            elif typing is Literal:
                choices = [str(v) for v in get_args(annotation)]
                response = await ctx.hitl.select(
                    tool_name=self.name,
                    message=f"Please choose an option for {field_description}",
                    choices=choices,
                    default=default_value or "",
                )
            else:
                msg = f"Please specify {field_description}"
                if not field.is_required():
                    msg += ". Leave blank to skip"
                response = await ctx.hitl.input(
                    tool_name=self.name,
                    message=msg,
                    default=default_value or "",
                )
                if not response:
                    response = "<NO_DATA>"

            results[key] = response

        return results

    async def _parse_instruction(self, ctx: Context, instruction: str):
        fn_reg = FunctionRegistration(
            fn=self.compose_configs,
            name="compose_configs",
            ctx_variables=[],
            ctx_param_name="ctx",
            description="make up user configuration criteria",
            model=self.model,
            schema=sanitize_schema(self.model),
        )

        messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=self.system_prompt,
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=instruction,
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
            raise RuntimeError("No tool call received to compose configs")

        args = json.loads(tool_calls[0].function.arguments)

        await ctx.send_debug_message(f"[{self.name}] Received {args}")

        return await self.compose_configs(ctx, **args)

    async def _finalize_configs(self, ctx: Context, configs: Dict[str, Any]):
        fn_reg = FunctionRegistration(
            fn=self.save_configs,
            name="save_configs",
            ctx_variables=[],
            ctx_param_name="ctx",
            description="Save the composed config fields into context",
            model=self.model,
            schema=sanitize_schema(self.model),
        )

        messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=dedent(
                    f"""
                    Compose and save config fields into context with the following steps:
                    
                    1. Parse the input provided in the JSON format to identify and extract 
                       necessary configuration criteria.
                    2. Convert each extracted field into its appropriate data type as 
                       specified by the schema.
                    3. Call the `save_configs` with the transformed config data.
                    """
                ),
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=json.dumps(configs),
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
            raise RuntimeError("No tool call received to save configs")

        args = json.loads(tool_calls[0].function.arguments)
        await ctx.send_debug_message(f"[{self.name}] Received {args}")

        return await self.save_configs(ctx, **args)

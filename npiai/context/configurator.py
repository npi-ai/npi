import json
import uuid
from textwrap import dedent
from typing import Any, Dict, Literal, get_origin, get_args, Type

from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel

from npiai.types import FunctionRegistration
from npiai.utils import sanitize_schema, get_type_annotation

from .context import Context


class Configurator:
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

    async def setup(self, ctx: Context, instruction: str) -> str:
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

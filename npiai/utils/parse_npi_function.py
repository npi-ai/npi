import dataclasses
import inspect
import re
from textwrap import dedent
from typing import Annotated, Callable, get_args, get_origin

import yaml
from pydantic import Field, create_model

from npiai.constant import CTX_QUERY_POSTFIX
from npiai.context import Context
from npiai.types import FunctionRegistration, Shot, ToolMeta, FromVectorDB
from npiai.utils import sanitize_schema, parse_docstring, is_template_str, to_async_fn


def parse_npi_function(
    fn: Callable,
    metadata: ToolMeta = ToolMeta(),
) -> FunctionRegistration:
    params = list(inspect.signature(fn).parameters.values())
    docstr = parse_docstring(inspect.getdoc(fn))
    tool_name = metadata.name or fn.__name__
    tool_desc = metadata.description or docstr.description

    if not tool_desc:
        raise ValueError(f"Unable to get the description of tool function `{fn}`")

    # parse schema
    tool_model = metadata.model
    tool_schema = metadata.schema
    ctx_param_name = None
    ctx_variables = []

    if not tool_model and len(params) > 0:
        # get parameter descriptions
        param_descriptions = {}
        for p in docstr.params:
            param_descriptions[p.arg_name] = p.description

        # get parameter field definitions
        param_fields = {}
        for p in params:
            if p.annotation is Context:
                ctx_param_name = p.name
                continue

            if get_origin(p.annotation) is Annotated:
                # extract context variables
                return_type, anno = get_args(p.annotation)
                if isinstance(anno, FromVectorDB):
                    ctx_variables.append(
                        dataclasses.replace(
                            anno,
                            name=p.name,
                            return_type=return_type,
                        )
                    )

                    if is_template_str(anno.query):
                        param_fields[f"{p.name}{CTX_QUERY_POSTFIX}"] = (
                            str,
                            Field(
                                default=anno.query,
                                description=dedent(
                                    f"""
                                    This parameter is a query to retrieve information from the memory storage.
                                    For the following query, you should replace the strings surrounded by braces
                                    `{{}}` with the information from current context.
                                    
                                    Query: {anno.query}
                                    """
                                ),
                            ),
                        )
                    continue

            param_fields[p.name] = (
                p.annotation,
                Field(
                    default=(
                        p.default if p.default is not inspect.Parameter.empty else ...
                    ),
                    description=param_descriptions.get(p.name, ""),
                ),
            )

        if len(param_fields):
            tool_model = create_model(f"{tool_name}_model", **param_fields)

    if not tool_schema and tool_model:
        tool_schema = sanitize_schema(tool_model)

    # parse examples
    tool_few_shots = metadata.few_shots
    doc_shots = [m for m in docstr.meta if m.args == ["few_shots"]]

    if not tool_few_shots and len(doc_shots) > 0:
        tool_few_shots = []

        for shot in doc_shots:
            items = re.findall(r"^\s*- ", shot.description, re.MULTILINE)
            if len(items) == 1:
                # remove leading '- ' to avoid indentation issues
                shot_data = yaml.safe_load(re.sub(r"^\s*- ", "", shot.description))
            else:
                shot_data = yaml.safe_load(shot.description)

            if not isinstance(shot_data, list):
                shot_data = [shot_data]

            for d in shot_data:
                tool_few_shots.append(Shot(**d))

    return FunctionRegistration(
        # wrap fn in an async wrapper
        fn=to_async_fn(fn),
        name=tool_name,
        ctx_variables=ctx_variables,
        ctx_param_name=ctx_param_name,
        description=tool_desc.strip(),
        schema=tool_schema,
        model=tool_model,
        few_shots=tool_few_shots,
    )

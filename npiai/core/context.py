"""This module contains the classes for the context and context message"""
import datetime
import uuid
import asyncio
from typing import List, Union, TYPE_CHECKING

from litellm.types.completion import ChatCompletionMessageParam
from npiai.core import callback
from npiai.core.base import BaseTool, Context

if TYPE_CHECKING:
    from npiai.core import BaseTool


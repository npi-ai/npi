import json
from textwrap import dedent
from typing import Dict, TYPE_CHECKING, TypeVar, Type, Any

from mem0 import Memory
from pydantic import create_model, Field

from npiai.utils import sanitize_schema, logger
from .base import BaseMemory

if TYPE_CHECKING:
    from npiai.context import Context

_T = TypeVar("_T")


class VectorDBMemory(BaseMemory):
    _memory: Memory
    _query_cache: Dict[str, Any]

    def __init__(self, context: "Context"):
        super().__init__(context)
        # TODO: init memory from config file
        self._memory = Memory()
        self._query_cache = {}

    async def _ask_human(self, query: str):
        """
        Ask human if no memory is found

        Args:
            query: Memory search query
        """

        res = await self._ctx.hitl.input(
            tool_name="Vector DB",
            message=f"Please provide the following information: {query}",
        )

        await self.save(f"Question: {query}? Answer: {res}")

    async def save(self, info: str):
        """
        Save the given information into memory

        Args:
            info: Information to save
        """
        m = self._memory.add(
            data=info,
            run_id=self._ctx.id,
            metadata={"raw": info},
            prompt=dedent(
                f"""
                Deduce the facts, preferences, and memories from the provided text.
                Just return the facts, preferences, and memories in bullet points:
                Natural language text: {info}
                
                Constraint for deducing facts, preferences, and memories:
                - The facts, preferences, and memories should be concise and informative.
                - Don't start by "The person likes Pizza". Instead, start with "Likes Pizza".
                - Don't remember the user/agent details provided. Only remember the facts, preferences, and memories.
                
                Deduced facts, preferences, and memories:
                """
            ),
        )
        # clear cache
        self._query_cache = {}
        logger.debug(f"Saved memory: {m}")

    async def retrieve(
        self,
        query: str,
        return_type: Type[_T] = str,
        constraints: str = None,
        _is_retry: bool = False,
    ) -> _T:
        """
        Search the vector db

        Args:
            query: Memory search query
            return_type: Return type of the result
            constraints: Search constraints
            _is_retry: Retry flag
        """
        cached_result = self._query_cache.get(query, None)

        if cached_result:
            return cached_result

        async def retry():
            if _is_retry:
                return

            # invoke HITL and retry
            await self._ask_human(query)
            return await self.retrieve(query, return_type, constraints, _is_retry=True)

        memories = self._memory.search(query, run_id=self._ctx.id, limit=10)
        logger.debug(f"Retrieved memories: {json.dumps(memories)}")

        if len(memories) == 0:
            logger.info(f"No memories found for query: {query}")
            return await retry()

        mem_str = "- " + "\n- ".join(
            "Extracted data: " + m["text"] + "\n Raw data: " + m["metadata"]["raw"]
            for m in memories
        )

        callback_model = create_model(
            "MemorySearchCallback",
            data=(
                return_type,
                Field(
                    default=None,
                    description="Retrieved memories. Set to `null` if no data is found.",
                ),
            ),
        )

        schema = sanitize_schema(callback_model)

        # TODO: use npi llm client?
        response = self._memory.llm.generate_response(
            tool_choice="required",
            messages=[
                {
                    "role": "system",
                    "content": dedent(
                        f"""
                        Optimize the functioning of a memory retrieval AI tool by adhering to the following guidelines for processing search queries:

                        1. Respond to search queries by invoking the `callback` function, supplying the required information within the `data` argument.
                        2. When delivering the `data`, aim for brevity and accuracy—only include the core details pertinent to the query.
                           - For instance, rather than "The capital of France is Paris," provide the succinct "Paris."
                        3. Ensure the content in `data` is an exact match to the search query.
                           - As an example, "The password for the Wi-Fi is '1234Abcd'" should only be returned if the query is "Wi-Fi password" and not for "macOS password" or any other password-related question.
                        4. Adhere to any specified constraints in the retrieval process.

                        ## Memories
                        """
                    )
                    + mem_str,
                },
                {
                    "role": "user",
                    "content": dedent(
                        f"""
                        Query: {query}
                        Constraints: {constraints}
                        """
                    ),
                },
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "callback",
                        "description": "Callback with retrieved information from the given memory",
                        "parameters": schema,
                    },
                }
            ],
        )

        tool_calls = response["tool_calls"]

        if not tool_calls or tool_calls[0]["name"] != "callback":
            logger.info(
                f"No LLM callback found for query: {query}. Response: {json.dumps(response)}"
            )
            return await retry()

        logger.debug(f"LLM callback: {json.dumps(tool_calls)}")

        data = tool_calls[0]["arguments"].get("data", None)

        if data is None:
            logger.info(f"No data found for query: {query}")
            return await retry()

        self._query_cache[query] = data

        return data

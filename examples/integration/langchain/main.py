import asyncio

from langchain import hub
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI

from npiai.tools.web import Chromium
from npiai.integration import langchain


async def main():
    async with Chromium(headless=False) as chromium:
        toolkit = langchain.create_tool(chromium)
        tools = toolkit.get_tools()
        print(tools)

        instructions = chromium.system_prompt
        base_prompt = hub.pull("langchain-ai/openai-functions-template")
        prompt = base_prompt.partial(instructions=instructions)

        llm = ChatOpenAI(temperature=0)

        agent = create_openai_functions_agent(llm, toolkit.get_tools(), prompt)

        agent_executor = AgentExecutor(
            agent=agent,
            tools=toolkit.get_tools(),
            verbose=True,
        )

        await agent_executor.ainvoke({"input": "Get top 10 posts at Hacker News."})


if __name__ == "__main__":
    asyncio.run(main())

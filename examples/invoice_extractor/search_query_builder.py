from npiai import FunctionTool, function, Context

from constants import QUERY


class SearchQueryBuilder(FunctionTool):
    name = "search_query_builder"

    description = """
    Build Gmail search query based on the search criteria. For example, 
    to search for emails from someone@example.com, you may invoke this agent with 
    `chat(instruction="search for emails sent by someone@example.com")`
    """

    system_prompt = """
    You are an agent helping user compose a Gmail search query by interpreting 
    natural language instructions. For any given instruction, you must:
        1. Identify and extract key search criteria from the user's instruction, 
           including `keywords`, `sender`, and any other pertinent details.
        2. Engage with the `get_criteria` tool, inputting identified criteria and 
           leaving unspecified fields as `None`. The tool will interact with the 
           user to define any missing information, so you should always call this
           tool even if no criteria are present.
        3. Receive the refined criteria from the `get_criteria` tool.
        4. Formulate a Gmail search query using the finalized criteria provided 
           by the tool. Note that you may need to use the `newer_than` or
           `older_than` filter if the criteria contains relative dates.
        5. Utilize the `save_query` tool to record the crafted search query.
       
    ## Example
    Instruction: search for emails sent by someone@example.com
    Steps:
        a. Extracted criteria: `sender="someone@example.com"`.
        b. Interaction with `get_criteria`: `get_criteria(sender="someone@example.com")`, 
           which may result in the following JSON object after communicating with the user:
           `{"sender": "someone@example.com", "keywords": "daily standup meeting", "start_date": "last week"}`.
        c. Formulate the Gmail search query using the criteria: 
           `from:someone@example.com newer_than:7d daily standup meeting`.
        d. Record the query: `save_query(query="from:someone@example.com newer_than:7d daily standup meeting")`.
        
    Instruction: None
    Steps:
        a. Interaction with `get_criteria`: `get_criteria()`, 
           which may result in the following JSON object after communicating with the user:
           `{"keywords": "github", "end_data": "2024/7/1"}`.
        b. Formulate the Gmail search query using the criteria: 
           `before:2024/7/1 github`.
        c. Record the query: `save_query(query="before:2024/7/1 github")`.
    """

    @function
    async def get_criteria(
        self,
        ctx: Context,
        keywords: str | None = None,
        sender: str | None = None,
        recipient: str | None = None,
        subject: str | None = None,
        label: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        has_pdf_attachments: bool | None = None,
    ):
        """
        Get Gmail search criteria.

        Args:
            ctx: NPi Context object.
            keywords: Keywords or phrases to search for.
            sender: Specify the sender.
            recipient: Specify a recipient.
            subject: Words in the subject line.
            label: The label that the email should have.
            start_date: Search for emails after this date.
            end_date: Search for emails before this date.
            has_pdf_attachments: Whether the email contains PDF attachments.
        """

        async def hitl_input(msg: str, default: str | None):
            return await ctx.hitl.input(
                ctx=ctx,
                tool_name=self.name,
                message=msg,
                default=default or "",
            )

        async def hitl_confirm(msg: str, default: bool | None):
            return await ctx.hitl.confirm(
                ctx=ctx,
                tool_name=self.name,
                message=msg,
                default=default or False,
            )

        await ctx.send_debug_message("Composing Gmail search query...")

        keywords = await hitl_input(
            msg="Please specify the keywords to include in the emails. Leave blank to skip",
            default=keywords,
        )

        sender = await hitl_input(
            msg="Please specify the sender. Leave blank to skip",
            default=sender,
        )

        recipient = await hitl_input(
            msg="Please specify a recipient. Leave blank to skip",
            default=recipient,
        )

        subject = await hitl_input(
            msg="Please specify the words to include in the subject line. Leave blank to skip",
            default=subject,
        )

        label = await hitl_input(
            msg="Please specify the label for the emails. Leave blank to skip",
            default=label,
        )

        start_date = await hitl_input(
            msg="Please specify the start date for the search. Leave blank to start from the first-ever email",
            default=start_date,
        )

        end_date = await hitl_input(
            msg="Please specify the end date for the search. Leave blank to end with the latest email",
            default=end_date,
        )

        has_pdf_attachments = await hitl_confirm(
            msg="Does the emails contain PDF attachments?",
            default=has_pdf_attachments,
        )

        filters = {
            "keywords": keywords,
            "sender": sender,
            "recipient": recipient,
            "subject": subject,
            "label": label,
            "start_date": start_date,
            "end_date": end_date,
            # "has_pdf_attachments": has_pdf_attachments,
        }

        criteria = {}

        # remove empty fields
        for k, v in filters.items():
            if v is not None and v != "":
                criteria[k] = filters[k]

        if has_pdf_attachments:
            criteria["filename"] = "*.pdf"
        return criteria

    @function
    async def save_query(self, ctx: Context, query: str):
        """
        Save the query into context storage.

        Args:
            ctx: NPi Context object.
            query: Gmail search query.
        """
        await ctx.kv.save(QUERY, query)

        return "Query saved"


if __name__ == "__main__":
    import asyncio
    from npiai import agent
    from npiai.hitl_handler import ConsoleHandler

    from debug_context import DebugContext

    async def main():
        async with agent.wrap(SearchQueryBuilder()) as tool:
            ctx = DebugContext()
            ctx.use_hitl(ConsoleHandler())

            await tool.chat(ctx, "search for emails containing invoice")

            print("query:", await ctx.kv.get(ctx, QUERY))

    asyncio.run(main())

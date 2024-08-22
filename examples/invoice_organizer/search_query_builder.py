from textwrap import dedent

from npiai import FunctionTool, function, Context

from constants import StorageKeys


class SearchQueryBuilder(FunctionTool):
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
            2. Engage with the `get_criteria` tool, inputting identified criteria and 
               leaving unspecified fields as `None`. The tool will interact with the 
               user to define any missing information, so you should always call this
               tool even if no criteria are present.
            3. Receive the refined criteria from the `get_criteria` tool.
            4. Formulate a Gmail search query using the finalized criteria provided 
               by the tool.
            5. Utilize the `save_query` tool to record the crafted search query.
            
        Note that you should only call each tool once during the process.
        
        ## How to construct Gmail search query
        
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
        - Attachment filename pattern: use `filename:<pattern>` filter
           
        ## Examples
        
        Instruction: search for emails sent by someone@example.com in the last week
        Steps:
            a. Extracted criteria: `sender="someone@example.com"`.
            b. Interaction with `get_criteria`: `get_criteria(sender="someone@example.com", start_date="last week")`, 
               which may result in the following JSON object after communicating with the user:
               `{"sender": "someone@example.com", "start_date": "last week"}`.
            c. Formulate the Gmail search query using the criteria: 
               `from:someone@example.com newer_than:7d daily`.
            d. Record the query: `save_query(query="from:someone@example.com newer_than:7d")`.
            
        Instruction: search for github emails from 2024/7/1 to yesterday
        Steps:
            a. Interaction with `get_criteria`: 
               `get_criteria(keywords="github", start_data="2024/7/1", end_date="yesterday")`, 
               which may result in the following JSON object after communicating with the user:
               `{"keywords": "github", "start_date": "2024/7/1", "end_date": "yesterday"}`.
            b. Formulate the Gmail search query using the criteria: 
               `after:2024/7/1 older_than:1d github`.
            c. Record the query: `save_query(query="after:2024/7/1 older_than:1d github")`.
        """
    )

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
        in_folder: str | None = "inbox",
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
            start_date: Search for emails received after this date.
            end_date: Search for emails received before this date.
            in_folder: Search for emails within this folder.
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

        in_folder = await hitl_input(
            msg="Please specify the folder to search in. Leave blank to skip",
            default=in_folder,
        )

        has_pdf_attachments = await hitl_confirm(
            msg="Do the emails contain PDF attachments?",
            default=has_pdf_attachments,
        )

        additional_preferences = await hitl_input(
            msg="Any additional criteria (e.g., unread emails only) for email search? Leave blank to skip",
            default=None,
        )

        filters = {
            "keywords": keywords,
            "sender": sender,
            "recipient": recipient,
            "subject": subject,
            "label": label,
            "start_date": start_date,
            "end_date": end_date,
            "in_folder": in_folder,
            "additional_preferences": additional_preferences,
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
        confirmed = await ctx.hitl.confirm(
            ctx=ctx,
            tool_name=self.name,
            message=f"Does the search query `{query}` look good to you?",
        )

        if not confirmed:
            query = await ctx.hitl.input(
                ctx=ctx,
                tool_name=self.name,
                message=f"Amend the search query",
                default=query,
            )

        await ctx.kv.save(StorageKeys.QUERY, query)

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

            print("query:", await ctx.kv.get(StorageKeys.QUERY))

    asyncio.run(main())

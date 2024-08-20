from typing import Literal, List

from npiai import FunctionTool, function, Context

from constants import StorageKeys


class OutputOptionsBuilder(FunctionTool):
    name = "output_options_builder"

    description = """
    Build data output options based on the search criteria. For example, 
    to export data as spreadsheets, you may invoke this agent with 
    `chat(instruction="output with spreadsheets")`
    """

    system_prompt = """
    You are an agent helping user configurate data output options by interpreting 
    natural language instructions. For any given instruction, you must:
        1. Identify and extract key criteria from the user's instruction, 
           including `format`, `destination`, and any other pertinent details.
        2. Engage with the `set_output_options` tool, inputting identified criteria and 
           leaving unspecified fields as `None`. The tool will interact with the 
           user to define any missing information, so you should always call this
           tool even if no criteria are present.
       
    ## Example
    Instruction: render the results as spreadsheets and save them to google drive
    Steps:
        a. Extracted criteria: `destination="google_drive"`.
        b. Interaction with `set_output_options`: 
           `set_output_options(format="spreadsheet", destination="google_drive")`
           
    Instruction: None
    Steps:
        a. Interaction with `set_output_options`: 
           `set_output_options()`
    """

    @function
    async def set_output_options(
        self,
        ctx: Context,
        format: Literal["spreadsheet", "csv", "json"] = None,
        destination: Literal["file", "google drive"] = None,
        filename: str = None,
    ):
        """
        Set data output options.

        Args:
            ctx: NPi Context object.
            format: Output format.
            destination: Output destination.
            filename: Output filename.
        """

        async def hitl_input(msg: str, default: str | None):
            return await ctx.hitl.input(
                ctx=ctx,
                tool_name=self.name,
                message=msg,
                default=default or "",
            )

        async def hitl_select(msg: str, choices: List[str], default: str | None):
            return await ctx.hitl.select(
                ctx=ctx,
                tool_name=self.name,
                message=msg,
                choices=choices,
                default=default or None,
            )

        await ctx.send_debug_message("Setting up output options...")

        format = await hitl_select(
            msg="Choose output format",
            choices=["spreadsheet", "csv", "json"],
            default=format,
        )

        destination = await hitl_select(
            msg="Choose output destination",
            choices=["file", "google drive"],
            default=destination,
        )

        default_filename = filename

        if not default_filename:
            match format:
                case "spreadsheet":
                    default_filename = "invoice.csv"
                case "csv":
                    default_filename = "invoice.csv"
                case "json":
                    default_filename = "invoice.json"

        filename = await hitl_input(
            msg="Name the output file",
            default=default_filename,
        )

        await ctx.kv.save(StorageKeys.OUTPUT_FORMAT, format)
        await ctx.kv.save(StorageKeys.OUTPUT_DESTINATION, destination)
        await ctx.kv.save(StorageKeys.OUTPUT_FILENAME, filename)

        return {
            "format": format,
            "destination": destination,
            "filename": filename,
        }


if __name__ == "__main__":
    import asyncio
    from npiai import agent
    from npiai.hitl_handler import ConsoleHandler

    from debug_context import DebugContext

    async def main():
        async with agent.wrap(OutputOptionsBuilder()) as tool:
            ctx = DebugContext()
            ctx.use_hitl(ConsoleHandler())

            await tool.chat(ctx, "no options provided")

            print("output format:", await ctx.kv.get(ctx, StorageKeys.OUTPUT_FORMAT))
            print(
                "output destination:",
                await ctx.kv.get(ctx, StorageKeys.OUTPUT_DESTINATION),
            )
            print(
                "output filename:", await ctx.kv.get(ctx, StorageKeys.OUTPUT_FILENAME)
            )

    asyncio.run(main())

from textwrap import dedent
from typing import Literal

from pydantic import BaseModel, Field

from constants import StorageKeys
from npiai import Configurator


class OutputConfigsModel(BaseModel):
    format: Literal["json", "csv", "spreadsheet"] = Field(
        default="json", description="Output format"
    )
    destination: Literal["file", "google drive"] = Field(
        default="file", description="Output destination"
    )
    filename: str = Field(default="data.json", description="Output filename")


class OutputConfigs(Configurator):
    model = OutputConfigsModel
    storage_key = StorageKeys.OUTPUT_OPTIONS
    description = "Output options for invoice processing"

    system_prompt = dedent(
        """
        You are an agent helping user configurate data output options by interpreting 
        natural language instructions. For any given instruction, you must:
            1. Identify and extract key criteria from the user's instruction, including 
               `format`, `destination`, and any other pertinent details. You may suggest
               a filename (e.g. 'results.json') if not provided.
            2. Engage with the `compose_configs` tool, inputting identified criteria and 
               leaving unspecified fields as `None`. The tool will interact with the 
               user to define any missing information, so you should always call this
               tool even if no criteria are present.
           
        ## Examples
        
        Instruction: render the results as spreadsheets and save them to google drive
        Steps:
            a. Extracted criteria: `destination="google_drive"`.
            b. Interaction with `compose_configs`:
               `compose_configs(format="spreadsheet", destination="google_drive")`
               
        Instruction: None
        Steps:
            a. Interaction with `compose_configs`:
               `compose_configs()`
        """
    )


if __name__ == "__main__":
    import asyncio
    from npiai.hitl_handler import ConsoleHandler

    from debug_context import DebugContext

    async def main():
        ctx = DebugContext()
        ctx.use_hitl(ConsoleHandler())
        ctx.use_configs(OutputConfigs())

        await ctx.setup_configs("save data to excel")

        print("Output options:", await ctx.kv.get(StorageKeys.OUTPUT_OPTIONS))

    asyncio.run(main())

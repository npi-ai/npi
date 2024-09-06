from textwrap import dedent

from pydantic import BaseModel, Field

from npiai import Configurator


class MeetingConfigsModel(BaseModel):
    attendee_name: str = Field(description="Name of the attendee")
    attendee_email: str = Field(description="Email of the attendee")
    date: str = Field(description="Date of the meeting")
    time: str = Field(description="Time of the meeting")
    duration: str = Field(description="Duration of the meeting")


class MeetingConfigs(Configurator):
    model = MeetingConfigsModel
    storage_key = "meeting_configs"
    description = "Meeting configuration for scheduling"

    system_prompt = dedent(
        """
        You are an agent helping user configurate meeting scheduling options by interpreting 
        natural language instructions. For any given instruction, you must:
            1. Identify and extract key criteria from the user's instruction, including 
               `date`, `time`, and any other pertinent details.
            2. Engage with the `compose_configs` tool, inputting identified criteria and 
               leaving unspecified fields as `None` or empty strings. The tool will interact with the 
               user to define any missing information, so you should always call this
               tool even if no criteria are present.
           
        ## Examples
        
        Instruction: schedule a meeting with John Doe on Monday at 2 PM for 1 hour
        Steps:
            a. Extracted criteria: `attendee_name="John Doe", date="Monday", time="2 PM", duration="1 hour"`.
            b. Interaction with `compose_configs`:
                `compose_configs(attendee_name="John Doe", date="Monday", time="2 PM", duration="1 hour")`
               
        Instruction: None
        Steps:
            a. Interaction with `compose_configs`:
               `compose_configs()`
        """
    )

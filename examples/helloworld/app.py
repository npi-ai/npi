from typing import List

from pydantic import Field
from npi.v1 import App
from npi.v1.types import Parameters, Shot


class GetTimezoneParameters(Parameters):
    test: str = Field(description="string parameter")
    cases: List[str] = Field(description="list of strings parameter")


def hello_world() -> App:
    app = App(
        name='time',
        description='a function package to get current date and timezone',
        provider='npiai',
    )

    @app.npi_tool(
        few_shots=[
            Shot(
                instruction='get current date',
                calling='get_today()',
                output='2024-05-18',
            )
        ]
    )
    def get_today():
        """Get today's date."""
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d")

    @app.npi_tool
    def get_timezone(params: GetTimezoneParameters):
        """Get the timezone name."""
        return params.test + ", America/New_York"

    return app


if __name__ == "__main__":
    hello_world().export_tools('.cache/function.yml')

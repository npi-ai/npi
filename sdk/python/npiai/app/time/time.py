from typing import List

from npiai.types import Shot
from npiai import NPI

from fastapi import FastAPI

app = FastAPI()

def create() -> NPI:
    app = NPI(
        name='time',
        description='a function package to get current date and timezone',
        provider='npiai',
    )

    @app.function(
        few_shots=[
            Shot(
                instruction='get current date',
                calling='get_today()',
                output='2024-05-18',
            )
        ]
    )
    def get_today():
        """
        Get today's date.

        FewShots:
        - instruction: Get today's date.
          calling: get_today()
          output: 2024-05-18
        """
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d")

    @app.function
    def get_timezone(test: str, cases: List[str]):
        """
        Get the timezone name.

        Args:
            test: String parameter test.
            cases: List of string parameters.
        """
        print(cases)
        return test + ", America/New_York"

    return app

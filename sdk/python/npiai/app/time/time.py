from typing import List

from npiai.types import Shot
from npiai import NPI


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
        """Get today's date."""
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d")

    @app.function
    def get_timezone(test: str, cases: List[str]):
        """
        Get the timezone name.

        FewShots:
        - instruction: Get the timezone name.
          calling: get_timezone('test', ['case1', 'case2'])
          output: test, America/New_York

        Args:
            test: String parameter test.
            cases: List of string parameters.
        """
        print(cases)
        return test + ", America/New_York"

    return app

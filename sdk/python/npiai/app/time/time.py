from typing import List

from npiai import NPi


def create() -> NPi:
    app = NPi(
        name='time',
        description='a function package to get current date and timezone',
        provider='npiai',
    )

    @app.function
    def get_today():
        """
        Get today's date.

        Few shots:
            - instruction: Get today's date.
              calling: |-
                get_today(
                    'asdf'
                )
              output: 2024-05-18

        Returns:
            None
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


if __name__ == '__main__':
    create().export('.cache/function.yml')

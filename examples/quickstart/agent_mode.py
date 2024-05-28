import os

from npiai import NPi
from npiai.app import time


def create_test_package() -> NPi:
    testpkg = NPi(
        name='test-pkg',
        description='a function package to get current date and timezone',
        provider='npiai',
    )

    @testpkg.function(description="demo")
    def test():
        return 'Hello NPi!'

    @testpkg.function(description="demo")
    def test2():
        return 'Hello NPi1111111!'

    return testpkg


if __name__ == '__main__':
    os.environ['OPENAI_API_KEY'] = 'abcdefg'
    npi = NPi(model="gpt-4o")

    npi.add(create_test_package())

    print(npi.debug(fn_name='test-pkg/test2'))

    npi.add(time.create())
    # agent mode, use npi as an agent
    npi.chat("hi, what's the date today?")

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
    npi = NPi()
    test_pkg = create_test_package()

    npi.add(test_pkg)

    print(
        npi.debug_sync(
            toolset=test_pkg.name,
            fn_name='test2'
        )
    )

    npi.add(time.create())
    # agent mode, use npi as an agent
    res = npi.chat_sync('What day is it today?')
    print(res)

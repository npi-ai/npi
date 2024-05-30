import os

from npiai.sync_npi import SyncNPi
from npiai.app import time


def create_test_package() -> SyncNPi:
    testpkg = SyncNPi(
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
    npi = SyncNPi()
    test_pkg = create_test_package()

    npi.add(test_pkg)

    print(
        npi.debug(
            toolset=test_pkg.name,
            fn_name='test2'
        )
    )

    npi.add(time.create())
    # agent mode, use npi as an agent
    res = npi.chat('What day is it today?')
    print(res)

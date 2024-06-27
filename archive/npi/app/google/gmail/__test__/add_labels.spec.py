import asyncio

from npi.app.google.gmail import Gmail


async def main():
    gmail = Gmail()
    return await gmail.chat('Add label "TEST" to the latest email from daofeng.wu@emory.edu')


if __name__ == '__main__':
    res = asyncio.run(main())
    print(res)

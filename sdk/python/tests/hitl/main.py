from npiai.app.google import Gmail
from npiai.core.hitl import ConsoleHITLHandler

if __name__ == '__main__':
    gmail = Gmail()
    gmail.hitl(handler=ConsoleHITLHandler())
    print(gmail.chat("send an email to a@example.com saying hello"))
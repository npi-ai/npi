# pylint: disable=missing-module-docstring
import json

from npi.app.google.calendar import GoogleCalendar
from npi.core.context import Thread

if __name__ == '__main__':
    gc = GoogleCalendar()
    ctx = Thread()
    gc.chat(message='get meetings of ww@lifecycle.sh in tomorrow', context=ctx)
    pt = ctx.plaintext()
    print(json.dumps(pt))

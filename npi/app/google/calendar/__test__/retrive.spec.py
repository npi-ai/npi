from npi.app.google.calendar import GoogleCalendar

if __name__ == '__main__':
    gc = GoogleCalendar()
    gc.chat(message='get meetings of ww@lifecycle.sh in tomorrow', context=None)

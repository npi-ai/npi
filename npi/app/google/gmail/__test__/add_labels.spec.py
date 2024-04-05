from npi.app.google.gmail import GmailApp

if __name__ == '__main__':
    gmail = GmailApp()
    res = gmail.chat('Add label "TEST" to the latest email from daofeng.wu@emory.edu')
    print(res)

from npi.app.google.gmail import Gmail

if __name__ == '__main__':
    gmail = Gmail()
    res = gmail.chat('Add label "TEST" to the latest email from daofeng.wu@emory.edu')
    print(res)

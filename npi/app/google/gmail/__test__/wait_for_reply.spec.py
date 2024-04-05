from npi.app.google.gmail import Gmail

if __name__ == '__main__':
    gmail = Gmail()
    first_res, hist = gmail.chat(
        'Send an email to daofeng.wu@emory.edu inviting him to join an AI meetup and wait for his reply. The date candidates are: Monday, Tuesday, Wednesday',
        return_history=True
    )
    final_res = gmail.chat('Wait for reply from the last message', context=hist)
    print(final_res)

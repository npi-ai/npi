from npi.app.github import GitHub

if __name__ == '__main__':
    github = GitHub()
    res = github.chat('Create a test issue in idiotWu/npi-test with label "NPi" and assign it to @idiotWu')
    print(res)

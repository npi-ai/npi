from npi.app.github import GitHub

if __name__ == '__main__':
    github = GitHub()
    res = github.chat('Close all pull requests in idiotWu/npi-test')
    print(res)

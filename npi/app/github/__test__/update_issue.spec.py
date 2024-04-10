from npi.app.github import GitHub

if __name__ == '__main__':
    github = GitHub()
    res = github.chat(
        'Find the issue in the repo idiotWu/npi-test titled "Test Issue for NPi" and change the body to "Hello World"'
    )
    print(res)

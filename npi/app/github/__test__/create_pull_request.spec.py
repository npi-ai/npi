from npi.app.github import GitHub

if __name__ == '__main__':
    github = GitHub()
    res = github.chat(
        'Create a pull request in idiotWu/npi-test from "npi-test" branch to "main" branch with random title and body'
    )
    print(res)

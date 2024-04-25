# NPI

> [!WARNING]
> NPi is currently under active development and the APIs are subject to change in the future release. It is recommended
> to use the command line tool to try it out.

NPi (**N**atural-language **P**rogramming **I**nterface), pronounced as **"N π"**, is an open-source platform providing
**_Tool-use_** APIs to empower AI agents with the ability to operate and interact with a diverse array of software tools
and applications.

## Quickstart

### Installation

#### Command Line Tool

Download the binary from the following links.

```sh
# For amr64
curl -O https://s.npi.ai/cli/v0.0.1/arm64/npi
# For amd64
curl -O https://s.npi.ai/cli/v0.0.1/amd64/npi
```

Then move it to `/usr/local/bin` or any other directory in your `PATH`:

```sh
chmod +x npi
sudo mv npi /usr/local/bin
```

Verify the installation by running `npi version`. If you see the output similar to the following, you are all set:

```json
{
  "BuildDate": "2024-04-23_02:23:50-0700",
  "GitCommit": "934739f",
  "Platform": "darwin/arm64",
  "Version": "v0.0.0"
}
```

#### Setting Up NPi Server with Docker

Replace `{YOUR_OAI_KEY}` with your actual OpenAI API Key, then execute:

```sh
docker run -d --name npi \
    -p 9140:9140 \
    -p 9141:9141 \
    -e OPENAI_API_KEY={YOUR_OAI_KEY} \
    npiai/npi
```

Confirm server connectivity by running `npi connect test`. If you receive a `server connected` message, the setup is
successful. Otherwise, consult the logs with `docker logs npi` and report issues
to [NPi GitHub Repository](https://github.com/npi-ai/npi/issues/new).

### Try the GitHub App

#### Authorize NPi to access your GitHub account

Generate a new token via [GitHub Tokens Page](https://github.com/settings/tokens) for NPi, and authorize NPi's access to
your GitHub account with:

```sh
npi auth github --access-token YOUR_GITHUB_ACCESS_TOKEN
```

#### Support the NPi Repository

Easily star and fork the NPi Repository using:

```sh
npi app github "Star, fork, and leave a supportive message in issue #27 of npi-ai/npi"
```

#### Clean up

1. Stop and remove the NPi container:
    ```sh
    docker stop npi
    docker rm npi
    ```
2. Revoke your GitHub access token by revisiting: [GitHub Tokens Page](https://github.com/settings/tokens).

## Python SDK

[NPI Python SDK](https://github.com/npi-ai/client-python)

## Multi-app Agent Examples

1. [Calendar Negotiator](examples/calendar_negotiator/main.py)
2. [Twitter Crawler](examples/twitter_crawler/main.py)

## License

[BSL v1.1](LICENSE).

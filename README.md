# NPI

> [!WARNING]
> NPi is currently under active development and the APIs are subject to change in the future release. It is recommended
> to use the command line tool to try it out.

NPi (**N**atural-language **P**rogramming **I**nterface), pronounced as **"N π"**, is an open-source platform providing
**_Tool-use_** APIs to empower AI agents with the ability to operate and interact with a diverse array of software tools
and applications.

[📢 Join our community on Discord](https://discord.gg/MQTuXtbj)

[👀 NPi Show cases](https://npi.ai/docs/examples)

## Quickstart

### Installation

#### Command Line Tool

Download the binary from the following links.

```sh
# For darwin/arm64
curl -O https://s.npi.ai/cli/latest/darwin/arm64/npi

# For darwin/amd64
curl -O https://s.npi.ai/cli/latest/darwin/amd64/npi

# For linux/arm64
curl -O https://s.npi.ai/cli/latest/linux/arm64/npi

# For linux/amd64
curl -O https://s.npi.ai/cli/latest/linux/amd64/npi

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
  "Version": "v0.0.1"
}
```

#### Setting Up NPi Server

> [!TIP]
> If Docker is not yet installed on your system, refer to the [Docker Installation Guide](https://docs.docker.com/get-docker/) for setup instructions.


Replace `YOUR_OAI_KEY` with your actual OpenAI API Key, then execute:

```sh
docker run -d --name npi --pull always \
    -p 9140:9140 \
    -p 9141:9141 \
    -e OPENAI_API_KEY=YOUR_OAI_KEY npiai/npi
```

For macOS users, use this command instead:

```sh
docker run -d --name npi --pull always \
   -p 9140:9140 \
   -p 9141:9141 \
   -e OPENAI_API_KEY=YOUR_OAI_KEY npiai/npi-mac
```

Confirm server connectivity by running `npi connect test`. If you receive a `NPi Server is operational!` message, the
setup is
successful. Otherwise, consult the logs with `docker logs npi` and report issues
to [NPi GitHub Repository](https://github.com/npi-ai/npi/issues/new).

### Try the GitHub App

#### Authorize NPi to access your GitHub account

Generate a new token via [GitHub Tokens Page](https://github.com/settings/tokens) for NPi, you may need to grant the `repo` scope so that NPi can access
repositories on behalf of you. ([Read more about scopes](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps))

![img.png](docs/assets/github-token-grant-repo.png)

Then, authorize NPi's access to your GitHub account with the following command:

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

More: https://docs.npi.ai/examples

## Roadmap

https://docs.npi.ai/roadmap

## License

[BSL v1.1](LICENSE).

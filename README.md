# NPI

NPI(pronunciation: N-π) is a platform providing Natural language Programming Interface to existing software.
We bring out-of-box **Tool use** APIs to Agent for enhancing its capability of using tools.

**Currently, NPi is unstable and API may change in the future release, so we recommend you using the command line tool to experience NPI.**

## Quickstart

### Installation

#### Command line tool
Download the binary from the following links.
```sh
# For amr64
wget https://s.npi.ai/cli/v0.0.1/arm64/npi
# For amd64
wget https://s.npi.ai/cli/v0.0.1/amd64/npi
```
then move it to `/usr/local/bin` or any other directory in your PATH
```sh
chmod +x npi
sudo mv npi /usr/local/bin
```

#### Server 

please replace `{YOUR_OAI_KEY}` with your OpenAI API Key
```sh
docker run -d --name npi \
-p 9140:9140 \
-p 9141:9141 \
-e OPENAI_API_KEY={YOUR_OAI_KEY} \
npiai/npi
```
run `npi connect test` to verify the installation. if `server connected` is printed, it means the installation is successful.
otherwise, please check the logs by running `docker logs npi` and create an issue [new issue](https://github.com/npi-ai/npi/issues/new)

### Chat with GitHub

#### Authorize your GitHub account

open [https://github.com/settings/tokens](https://github.com/settings/tokens) create a new token for NPi, and use the
following command to authorize NPi to access your GitHub account.

```sh
npi auth github --access-token YOUR_GITHUB_ACCESS_TOKEN
```

### Star and fork NPi Repo

use this command to star and fork the NPi Repo

```sh
npi app github "star and fork the repo of npi-ai/npi"
```

you will enter an interactive mode to chat with GitHub.

### Clean up

1. stop and remove the NPi container
```sh
docker stop npi
docker rm npi
```

2. remove your GitHub access token [https://github.com/settings/tokens](https://github.com/settings/tokens).

## Python SDK
[NPI Python SDK](https://github.com/npi-ai/client-python)

## Examples

1. [Calendar Negotiator](examples/calendar_negotiator/main.py)
2. [Twitter Bot](examples/twitter_bot/main.py)

## License

BSL v1.1, see [LICENSE](LICENSE).
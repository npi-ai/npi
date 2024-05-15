FROM --platform=$BUILDPLATFORM python:3.10

LABEL maintainer="Wenfeng Wang <w@npi.ai>"

RUN apt update
RUN apt install curl vim wget pipx -y
RUN pipx install poetry

ENV PATH="/root/.local/bin:${PATH}"
RUN poetry run playwright install-deps chromium
RUN poetry run playwright install chromium
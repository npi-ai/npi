FROM --platform=$BUILDPLATFORM python:3.12

LABEL maintainer="Wenfeng Wang <w@npi.ai>"

COPY ./playwright /root/playwright

WORKDIR /root/playwright

RUN apt update
RUN apt install curl vim wget pipx -y
RUN pipx install poetry
ENV PATH="/root/.local/bin:${PATH}"

RUN poetry install
RUN poetry run playwright install-deps chromium
RUN poetry run playwright install chromium

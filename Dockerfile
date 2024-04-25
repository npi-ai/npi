FROM --platform=$BUILDPLATFORM python:3.10

LABEL maintainer="Wenfeng Wang <w@npi.ai>"

COPY . /npiai
WORKDIR /npiai

RUN apt update
RUN apt install curl vim wget pipx -y
RUN pipx install poetry
ENV PATH="/root/.local/bin:${PATH}"
RUN poetry install
RUN poetry run playwright install chromium
RUN poetry run playwright install-deps

ENV NPI_CONFIG_FILE="/npiai/config/config.yaml"

CMD ["poetry", "run", "server"]

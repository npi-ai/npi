FROM --platform=$BUILDPLATFORM python:3.10

LABEL maintainer="Wenfeng Wang <w@npi.ai>"

COPY . /npiai
WORKDIR /npiai

RUN apt update
RUN apt install curl vim wget pipx -y
RUN pipx install poetry
ENV PATH="/root/.local/bin:${PATH}"
RUN poetry install

ENV NPI_CONFIG_FILE="/npiai/config/config.yaml"

CMD ["poetry", "run", "server"]
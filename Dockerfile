FROM npiai/base:3.10

LABEL maintainer="Wenfeng Wang <w@npi.ai>"

COPY . /npiai
WORKDIR /npiai

ENV PATH="/root/.local/bin:${PATH}"
RUN poetry install
RUN poetry run playwright install chromium
RUN poetry run playwright install-deps chromium

ENV NPI_CONFIG_FILE="/npiai/config/config.yaml"

CMD ["poetry", "run", "server"]

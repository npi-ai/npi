FROM --platform=$BUILDPLATFORM npiai/python:3.12

LABEL maintainer="Wenfeng Wang <w@npi.ai>"

COPY . /npi/

WORKDIR /npi

RUN poetry install
ENV PATH="/root/.cache/pypoetry/virtualenvs/npiai-Gwe6qz7c-py3.11/bin:${PATH}"
RUN playwright install-deps chromium
RUN playwright install chromium

ENTRYPOINT ["python", "playground/main.py"]

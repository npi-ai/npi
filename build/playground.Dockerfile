FROM --platform=$BUILDPLATFORM npiai/python:3.12

LABEL maintainer="Wenfeng Wang <w@npi.ai>"

COPY . /npi/

WORKDIR /npi

RUN poetry install

ENTRYPOINT ["poetry", "run", "python", "playground/main.py"]

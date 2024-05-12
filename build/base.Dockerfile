FROM --platform=$BUILDPLATFORM python:3.10

LABEL maintainer="Wenfeng Wang <w@npi.ai>"

RUN apt update
RUN apt install curl vim wget pipx -y
RUN pipx install poetry
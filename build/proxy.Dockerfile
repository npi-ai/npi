FROM --platform=linux/amd64 ubuntu:22.04

COPY ./proxy /npi/proxy

RUN chmod +x /npi/proxy
RUN apt update
RUN apt install -y ca-certificates
RUN update-ca-certificates

ENTRYPOINT ["/npi/proxy"]
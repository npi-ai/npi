FROM --platform=$BUILDPLATFORM golang as builder

LABEL maintainer="Wenfeng Wang <w@npi.ai>"

COPY . /npiai

WORKDIR /npiai

RUN GOOS=linux GOARCH=amd64 go build -o gateway main.go

FROM --platform=$BUILDPLATFORM ubuntu:22.04

COPY --from=builder /npiai/gateway /npiai/gateway

CMD ["/npiai/gateway"]

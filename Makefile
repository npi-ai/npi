NPI_CMD_ROOT = $(shell pwd)
GIT_COMMIT = $(shell git log -1 --format='%h' | awk '{print $0}')
DOCKER_REGISTRY ?= 992297059634.dkr.ecr.us-west-2.amazonaws.com
DOCKER_PLATFORM ?= linux/arm64,linux/amd64
IMAGE_TAG ?= ${GIT_COMMIT}

build-docker-python:
	docker buildx build --platform ${DOCKER_PLATFORM} \
		-t npiai/python:3.12 -f build/base.Dockerfile build --push

build-docker-playground:
	docker buildx build --platform ${DOCKER_PLATFORM} \
		-t ${DOCKER_REGISTRY}/playground:${IMAGE_TAG} \
		-f build/playground.Dockerfile . --push

docker-build-proxy:
	GOOS=linux GOARCH=amd64 go build -C ${NPI_CMD_ROOT}/playground -trimpath -o bin/proxy  proxy.go
	docker build -t ${DOCKER_REGISTRY}/proxy:latest -f build/proxy.Dockerfile ${NPI_CMD_ROOT}/playground/bin
	docker push ${DOCKER_REGISTRY}/proxy:latest

release:
	poetry publish --build -u __token__ -p ${PYPI_TOKEN}
	rm -rf dist
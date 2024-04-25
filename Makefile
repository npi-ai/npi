NPI_CMD_ROOT = $(shell pwd)
GIT_COMMIT = $(shell git log -1 --format='%h' | awk '{print $0}')
DATE = $(shell date +%Y-%m-%d_%H:%M:%S%z)

VERSION ?= ${GIT_COMMIT}
IMAGE_TAG ?= ${VERSION}

#os linux or darwin
GOOS ?= darwin
#arch amd64 or arm64
GOARCH ?= arm64

CMD_OUTPUT_DIR ?= ${NPI_CMD_ROOT}/bin

LD_FLAGS = -X 'main.Version=${VERSION}'
LD_FLAGS += -X 'main.GitCommit=${GIT_COMMIT}'
LD_FLAGS += -X 'main.BuildDate=${DATE}'
LD_FLAGS += -X 'main.Platform=${GOOS}/${GOARCH}'

GO_BUILD = GOOS=$(GOOS) GOARCH=$(GOARCH) go build -C ${NPI_CMD_ROOT}/cli -trimpath
DOCKER_PLATFORM ?= linux/amd64,linux/arm64

build-npi:
	$(GO_BUILD) -ldflags "${LD_FLAGS}"  -o ${CMD_OUTPUT_DIR}/npi ${NPI_CMD_ROOT}/cli

docker-build:
	docker buildx build --platform ${DOCKER_PLATFORM} -t npiai/npi:${IMAGE_TAG} . --push

docker-build-local:
	docker build -t npiai/npi:${IMAGE_TAG} .

clean:
	rm -rf bin
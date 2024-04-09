NPI_CMD_ROOT = $(shell pwd)
GIT_COMMIT = $(shell git log -1 --format='%h' | awk '{print $0}')
DATE = $(shell date +%Y-%m-%d_%H:%M:%S%z)

DOCKER_REGISTRY ?= public.ecr.aws
DOCKER_REPO ?= ${DOCKER_REGISTRY}/npi
IMAGE_PREFIX ?=
IMAGE_TAG ?= ${GIT_COMMIT}
VERSION ?= ${IMAGE_TAG}

#os linux or darwin
GOOS ?= darwin
#arch amd64 or arm64
GOARCH ?= arm64

CMD_OUTPUT_DIR ?= ${NPI_CMD_ROOT}/bin

LD_FLAGS = -X 'main.Version=${VERSION}'
LD_FLAGS += -X 'main.GitCommit=${GIT_COMMIT}'
LD_FLAGS += -X 'main.BuildDate=${DATE}'
LD_FLAGS += -X 'main.Platform=${GOOS}/${GOARCH}'

GO_BUILD = GO111MODULE=on CGO_ENABLED=0 GOOS=$(GOOS) GOARCH=$(GOARCH) go build -trimpath


build-npi:
	$(GO_BUILD) -ldflags "${LD_FLAGS}" -o ${CMD_OUTPUT_DIR}/npi ${NPI_CMD_ROOT}/

clean:
	rm -rf bin
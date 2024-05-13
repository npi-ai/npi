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
DOCKER_PLATFORM ?= linux/arm64,linux/amd64

build-npi:
	$(GO_BUILD) -ldflags "${LD_FLAGS}"  -o ${CMD_OUTPUT_DIR}/npi ${NPI_CMD_ROOT}/cli

release-npi-cli:
	$(GO_BUILD) -ldflags "${LD_FLAGS}" -o ${CMD_OUTPUT_DIR}/cli/npi ${NPI_CMD_ROOT}/cli
	zip -j ${CMD_OUTPUT_DIR}/npi-${VERSION}-${GOOS}-${GOARCH}.zip ${CMD_OUTPUT_DIR}/npi

docker-build-x86:
	docker buildx build --platform linux/amd64 -t npiai/npi:${IMAGE_TAG} . --push

docker-build-arm:
	docker build --platform linux/arm/v8 --build-arg platform=linux/arm/v8 -t npiai/npi:${IMAGE_TAG} .
	docker push npiai/npi:${IMAGE_TAG}

docker-build-base-x86:
	docker build --platform linux/amd64 \
		--build-arg platform=linux/amd64 \
		-t npiai/base:3.10 -f build/base.Dockerfile build

docker-build-base:
	docker buildx build --platform ${DOCKER_PLATFORM} -t npiai/base:3.10 -f build/base.Dockerfile build --push
	#docker push npiai/base:3.10

docker-build-local:
	docker build -t npiai/npi:${IMAGE_TAG} .

clean:
	rm -rf bin
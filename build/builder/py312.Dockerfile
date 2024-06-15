# docker buildx build --platform linux/amd64 -t npiai/python:3.12 -f py312.Dockerfile . --push
FROM python:3.12-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry
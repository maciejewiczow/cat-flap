FROM ghcr.io/astral-sh/uv:python3.13-bookworm AS build
ARG APP_SERVICE_NAME

ENV SOCKETS_DIR=/var/run/cat-flap/sockets

RUN apt update && apt install build-essential libcap-dev -y

WORKDIR /source

COPY ./$APP_SERVICE_NAME ./$APP_SERVICE_NAME
COPY ./shared ./shared
COPY ./scripts ./scripts
COPY pyproject.toml ./pyproject.toml.source

RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    app

RUN chown -R app:app /source

RUN mkdir -p /var/run/cat-flap/sockets

RUN mkdir -p /var/log/cat-flap

RUN mkdir /data

RUN chown app:app /var/log/cat-flap

RUN chown app:app /var/run/cat-flap/sockets

RUN chown app:app /data

ENV UV_TARGET_PLATFORM=linux-aarch64

RUN uv sync --directory ./scripts --no-dev
RUN uv run --directory ./scripts create-temp-pyproject.py ../pyproject.toml.source $APP_SERVICE_NAME

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev

RUN uv sync --directory $APP_SERVICE_NAME --no-dev

USER app

FROM python:3.13.11-slim
ARG APP_SERVICE_NAME

COPY --from=build --chown=app:app /source /source

WORKDIR /source

ENV COMMAND="source .venv/bin/activate && python ${APP_SERVICE_NAME}/main.py"

CMD $COMMAND

FROM ghcr.io/astral-sh/uv:python3.13-bookworm AS build
ARG APP_SERVICE_NAME

RUN apt update && apt install build-essential libcap-dev -y

WORKDIR /source

COPY ./$APP_SERVICE_NAME ./$APP_SERVICE_NAME
COPY ./shared ./shared
COPY ./scripts ./scripts
COPY pyproject.toml ./pyproject.toml.source

ENV UV_TARGET_PLATFORM=linux-aarch64
ENV UV_BREAK_SYSTEM_PACKAGES=true

RUN uv sync --directory ./scripts --no-dev && \
    uv run --directory ./scripts create-temp-pyproject.py ../pyproject.toml.source $APP_SERVICE_NAME &&\
    uv venv -p /usr/bin/python3 --system-site-packages

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev && \
    uv sync --directory $APP_SERVICE_NAME --no-dev

FROM mafciejewiczow/raspberrypi-os:python3.13-trixie
ARG APP_SERVICE_NAME

ENV SOCKETS_DIR=/var/run/cat-flap/sockets

RUN mkdir -p $SOCKETS_DIR && \
    mkdir -p /var/log/cat-flap && \
    mkdir /data

COPY --from=build /source /source

WORKDIR /source

ENV COMMAND=".venv/bin/python ${APP_SERVICE_NAME}/main.py"

CMD $COMMAND

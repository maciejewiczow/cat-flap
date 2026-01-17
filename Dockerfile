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
# ENV UV_PROJECT_ENVIRONMENT=/usr/lib/python3/dist-packages

RUN uv sync --directory ./scripts --no-dev
RUN uv run --directory ./scripts create-temp-pyproject.py ../pyproject.toml.source $APP_SERVICE_NAME

RUN uv venv -p /usr/bin/python3 --system-site-packages

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev

RUN uv sync --directory $APP_SERVICE_NAME --no-dev

FROM dtcooper/raspberrypi-os:python3.13-bookworm
ARG APP_SERVICE_NAME

ENV SOCKETS_DIR=/var/run/cat-flap/sockets

RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    app

RUN mkdir -p $SOCKETS_DIR

RUN mkdir -p /var/log/cat-flap

RUN mkdir /data

RUN chown app:app /var/log/cat-flap

RUN chown app:app $SOCKETS_DIR

RUN chown app:app /data

USER app

COPY --from=build --chown=app:app /source /source
COPY --from=build /usr /usr

WORKDIR /source

ENV COMMAND=".venv/bin/python ${APP_SERVICE_NAME}/main.py"

CMD $COMMAND

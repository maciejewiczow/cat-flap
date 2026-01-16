FROM ghcr.io/astral-sh/uv:alpine3.22
ARG APP_SERVICE_NAME

ENV SOCKETS_DIR=/var/run/cat-flap/sockets

WORKDIR /source

COPY ./$APP_SERVICE_NAME ./$APP_SERVICE_NAME
COPY ./shared ./shared
COPY ./scripts ./scripts
COPY pyproject.toml ./pyproject.toml.source

RUN addgroup -S app && adduser -S app -G app

RUN chown -R app:app /source

RUN mkdir -p /var/run/cat-flap/sockets

RUN mkdir -p /var/log/cat-flap

RUN mkdir /data

RUN chown app:app /var/log/cat-flap

RUN chown app:app /var/run/cat-flap/sockets

RUN chown app:app /data

USER app

RUN uv sync --directory ./scripts

RUN uv run --directory ./scripts create-temp-pyproject.py ../pyproject.toml.source $APP_SERVICE_NAME

RUN uv sync

RUN uv sync --directory $APP_SERVICE_NAME --no-dev

ENV COMMAND="uv run ${APP_SERVICE_NAME}/main.py"

CMD $COMMAND

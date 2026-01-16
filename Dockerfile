FROM ghcr.io/astral-sh/uv:alpine3.22
ARG APP_SERVICE_NAME

ENV SOCKETS_DIR=/var/run/cat-flap/sockets

WORKDIR /source

COPY ./$APP_SERVICE_NAME ./$APP_SERVICE_NAME
COPY ./shared ./shared
COPY ./scripts ./scripts
COPY pyproject.toml ./pyproject.toml.source

RUN uv sync --directory ./scripts

RUN uv run --directory ./scripts create-temp-pyproject.py ../pyproject.toml.source $APP_SERVICE_NAME

RUN uv sync

RUN adduser -D -g "Application" -G app app

RUN chown -R app:app /source

USER app

CMD ["uv", "run", "$APP_SERVICE_NAME/main.py"]

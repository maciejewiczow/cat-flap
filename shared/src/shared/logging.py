import logging
from logging import Logger
import logging.handlers
from os import environ, makedirs
import sys

logging.basicConfig(
    level=environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s [%(name)s] (%(funcName)s) %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def get_logger(name: str):
    log = Logger(name)

    dirname = environ.get("LOG_FOLDER", "/var/log/cat-flap")

    makedirs(dirname, exist_ok=True)

    log.addHandler(
        logging.handlers.RotatingFileHandler(
            f"{dirname}/{environ.get('LOG_FILE_NAME', name)}.log",
            maxBytes=20_000_000,
            backupCount=3,
        )
    )

    return log

import logging
import logging.handlers
from os import environ, makedirs
import sys

LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s] (%(funcName)s) %(message)s"

LOG_LEVEL = environ.get("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)],
)


def get_logger(name: str):
    log = logging.getLogger(name)

    dirname = environ.get("LOG_FOLDER", "/var/log/cat-flap")

    makedirs(dirname, exist_ok=True)

    file_handler = logging.handlers.RotatingFileHandler(
        f"{dirname}/{environ.get('LOG_FILE_NAME', name)}.log",
        maxBytes=20_000_000,
        backupCount=3,
    )
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    log.addHandler(file_handler)

    return log

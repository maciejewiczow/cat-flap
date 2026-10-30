from os import environ
from shared.hub import HubProcessMessageHub
from shared.logging import get_logger


log = get_logger("hub")


def main():
    try:
        log.info("Starting the hub process")
        hub = HubProcessMessageHub(environ["SOCKETS_DIR"])

        hub.run_hub()
    except:  # noqa: E722
        log.exception("An exception was thrown")


if __name__ == "__main__":
    main()

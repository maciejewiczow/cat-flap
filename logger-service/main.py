from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.main_fn import worker_main
from shared.messages import Message

log = get_logger("event-logger")


async def handle_messages(hub: WorkerMessageHub):
    log.info("Starting the logger service")

    async for message in hub.receive():
        log.debug(f"Received an object {message}")
        match message:
            case Message():
                log.debug(
                    f"Received message of type {type(message).__name__}: {message}",
                )
                continue

        log.warning(f"Received an object not of the Message class: {message}")


if __name__ == "__main__":
    worker_main(log, handle_messages)

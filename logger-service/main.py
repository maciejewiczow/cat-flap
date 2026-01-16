from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.main_fn import worker_main
from shared.messages import ImageCapturedMessage, InferenceCompleteMessage, Message

log = get_logger("event-logger")


async def handle_messages(hub: WorkerMessageHub):
    log.info("Starting the logger service")

    async for message in hub.receive():
        match message:
            case ImageCapturedMessage():
                log.debug(
                    f"Received message of type {type(message).__name__} at {message.timestamp.isoformat()}"
                )
            case InferenceCompleteMessage():
                log.debug(
                    f"Received message of type {type(message).__name__} at {message.timestamp.isoformat()}"
                )
            case Message():
                log.debug(
                    f"Received message of type {type(message).__name__}: {message}",
                )
                continue

        log.warning(f"Received an object not of the Message class: {message}")


if __name__ == "__main__":
    worker_main(log, handle_messages)

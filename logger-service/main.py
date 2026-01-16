from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.main_fn import worker_main
from shared.messages import Message

log = get_logger("event-logger")


async def handle_messages(hub: WorkerMessageHub):
    async for message in hub.receive():
        match message:
            case Message():
                log.debug(
                    f"Received message of type {type(message).__name__}",
                    extra={"message": message, "type": type(message).__name__},
                )


if __name__ == "__main__":
    worker_main(log, handle_messages)

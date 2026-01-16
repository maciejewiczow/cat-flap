from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.messages import ImageCapturedMessage, InferenceCompleteMessage
from shared.main_fn import worker_main

log = get_logger("diodes")


async def handle_messages(hub: WorkerMessageHub):
    async for message in hub.receive():
        match message:
            case ImageCapturedMessage():
                pass
            case InferenceCompleteMessage():
                pass


if __name__ == "__main__":
    worker_main(log, handle_messages)

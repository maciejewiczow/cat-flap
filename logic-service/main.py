import asyncio
from os import environ
from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.main_fn import worker_main
from shared.messages import (
    DoorClosedMessage,
    DoorOpenedMessage,
    InferenceCompleteMessage,
    MotionDetectedMessage,
    MotionEndedMessage,
    StartCaptureMessage,
)
from shared.utils.str_to_timedelta import str_to_timedelta

log = get_logger("logic")

state_file_path = "/data/state.json"

capture_interval = str_to_timedelta(environ.get("CAPTURE_INTERVAL", "2s"))


async def produce_capture_events(hub: WorkerMessageHub):
    try:
        while True:
            await hub.send(StartCaptureMessage())
            await asyncio.sleep(
                float(capture_interval.seconds)
                + capture_interval.microseconds / 1_000_000
            )
    except asyncio.CancelledError:
        return


async def handle_messages(hub: WorkerMessageHub):
    door_open = False
    capture_task: asyncio.Task[None] | None = None
    loop = asyncio.get_event_loop()

    async for message in hub.receive():
        match message:
            case MotionDetectedMessage():
                if not door_open:
                    log.info("Door not opened, starting image capturing")
                    capture_task = loop.create_task(produce_capture_events(hub))
                elif capture_task is not None:
                    capture_task.cancel()

            case MotionEndedMessage():
                if capture_task is not None:
                    capture_task.cancel()

            case DoorOpenedMessage():
                log.info("Detected that the door are open")
                door_open = True

            case DoorClosedMessage():
                log.info("Detected that the door were closed")
                door_open = False

            case InferenceCompleteMessage(detected_classes=classes):
                log.info(f"Inference completed, classes detected: {classes}")


if __name__ == "__main__":
    worker_main(log, handle_messages)

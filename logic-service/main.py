import asyncio
from os import environ
from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.main_fn import worker_main
from shared.messages import (
    DoorClosedMessage,
    DoorOpenedMessage,
    InferenceCompleteMessage,
    LockFlapMessage,
    MotionDetectedMessage,
    MotionEndedMessage,
    StartCaptureMessage,
    UnlockFlapMessage,
)
from shared.utils.str_to_timedelta import str_to_timedelta

log = get_logger("logic")

capture_interval = str_to_timedelta(environ.get("CAPTURE_INTERVAL", "2s"))
lockout_duration = str_to_timedelta(environ.get("LOCKOUT_DURATION", "20s"))


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


async def wait_for_lockout(hub: WorkerMessageHub):
    try:
        await asyncio.sleep(lockout_duration.seconds)
        await hub.send(UnlockFlapMessage())
    except asyncio.CancelledError:
        return


async def handle_messages(hub: WorkerMessageHub):
    door_open = False
    capture_task: asyncio.Task[None] | None = None
    unlock_flap_task: asyncio.Task[None] | None = None

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

                prey_classes = [item for item in classes if item[0] == "prey"]

                if len(prey_classes) > 0:
                    max_prey_prob = max(
                        (prob for _, prob in prey_classes),
                    )

                    if max_prey_prob > 0.5:
                        await hub.send(LockFlapMessage())

                        if unlock_flap_task is not None:
                            unlock_flap_task.cancel()

                        unlock_flap_task = loop.create_task(wait_for_lockout(hub))
                    else:
                        log.warning(
                            f"Prey detected with low probability ({max_prey_prob:.2%}), not locking the flap"
                        )
                else:
                    if unlock_flap_task is not None:
                        unlock_flap_task.cancel()

                    await hub.send(UnlockFlapMessage())


if __name__ == "__main__":
    worker_main(log, handle_messages)

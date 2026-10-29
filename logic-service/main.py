import asyncio
from os import environ

from statemachine import State

from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.main_fn import worker_main
from shared.messages import (
    DoorClosedMessage,
    DoorOpenedMessage,
    InferenceCompleteMessage,
    EngageLockMessage,
    MainButtonPressedMessage,
    MotionDetectedMessage,
    MotionEndedMessage,
    StartCaptureMessage,
    DisengageLockMessage,
    StateUpdate,
)
from shared.state import CatFlapStateMachine
from shared.utils.str_to_timedelta import str_to_timedelta

log = get_logger("logic")

capture_interval = str_to_timedelta(environ.get("CAPTURE_INTERVAL", "2s"))
lockout_duration = str_to_timedelta(environ.get("LOCKOUT_DURATION", "20s"))


class StateUpdateListener:
    def __init__(self, hub: WorkerMessageHub):
        self.hub = hub

    async def on_enter_state(
        self, source: State, target: State, machine: CatFlapStateMachine
    ):
        log.info(f"State changed: {source} -> {target}")
        await self.hub.send(StateUpdate(new_state=machine))


class MessageSenderListener:
    def __init__(self, hub: WorkerMessageHub):
        self.hub = hub

    async def on_enter_movement_detected(self, source: State):
        await self.hub.send(StartCaptureMessage())


async def handle_messages(hub: WorkerMessageHub, state: CatFlapStateMachine):
    log.info("Starting the logic service")

    state.add_listener(StateUpdateListener(hub))
    state.add_listener(MessageSenderListener(hub))

    async for message in hub.receive():
        match message:
            case MotionDetectedMessage():
                state.movement()

            case MotionEndedMessage():
                state.movement_ended()

            case DoorOpenedMessage():
                log.info("Detected that the door are open")
                state.door_opened()

            case DoorClosedMessage():
                log.info("Detected that the door were closed")
                state.door_closed()

            case MainButtonPressedMessage():
                if state.is_disabled:
                    log.info("Main button pressed, enabling the system")
                    state.enable()
                else:
                    log.info("Main button pressed, disabling the system")
                    state.disable()

            case InferenceCompleteMessage(detected_classes=classes):
                log.info(f"Inference completed, classes detected: {classes}")

                prey_classes = [item for item in classes if item[0] == "prey"]

                if len(prey_classes) > 0:
                    max_prey_prob = max(
                        (prob for _, prob in prey_classes),
                    )

                    if max_prey_prob > 0.5:
                        log.info(
                            f"Prey detected with high probability ({max_prey_prob:.2%}), locking the flap"
                        )
                        state.prey_detected()
                    else:
                        log.warning(
                            f"Prey detected with low probability ({max_prey_prob:.2%}), not locking the flap"
                        )
                        state.no_prey()
                else:
                    log.info("No prey detected, not locking the flap")
                    state.no_prey()


if __name__ == "__main__":
    worker_main(log, handle_messages)

import asyncio
from concurrent.futures import Future
from os import environ

from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.main_fn import worker_main
from shared.messages import (
    DisengageLockMessage,
    DoorClosedMessage,
    DoorOpenedMessage,
    EngageLockMessage,
    InferenceCompleteMessage,
    MainButtonPressedMessage,
    Message,
    MotionDetectedMessage,
    MotionEndedMessage,
    StartCaptureMessage,
    StateUpdate,
)
from shared.state import CatFlapStateMachine
from shared.utils.str_to_timedelta import str_to_timedelta
from statemachine import State

log = get_logger("logic")

capture_interval = str_to_timedelta(environ.get("CAPTURE_INTERVAL", "2s"))
lockout_duration = str_to_timedelta(environ.get("LOCKOUT_DURATION", "20s"))
prey_lockout_probability = float(
    environ.get("PREY_PROBABILITY_REQUIRED_FOR_LOCKOUT", "0.5")
)


def _schedule_send(
    loop: asyncio.AbstractEventLoop, hub: WorkerMessageHub, message: Message
):
    future = asyncio.run_coroutine_threadsafe(hub.send(message), loop)
    future.add_done_callback(_log_send_failure)


def _log_send_failure(future: Future[None]):
    try:
        future.result()
    except Exception:
        log.exception("Failed to send a message from the logic service")


class StateUpdateListener:
    def __init__(self, hub: WorkerMessageHub, loop: asyncio.AbstractEventLoop):
        self.hub = hub
        self.loop = loop

    def on_enter_state(
        self, source: State, target: State, machine: CatFlapStateMachine
    ):
        log.info(f"State changed: {source} -> {target}")
        state_snapshot = CatFlapStateMachine()
        state_snapshot.current_state_value = machine.current_state_value
        _schedule_send(self.loop, self.hub, StateUpdate(new_state=state_snapshot))


class MessageSenderListener:
    def __init__(
        self,
        hub: WorkerMessageHub,
        loop: asyncio.AbstractEventLoop,
        lock_engaged: bool = False,
    ):
        self.hub = hub
        self.loop = loop
        self.lock_engaged = lock_engaged

    def on_enter_state(
        self, source: State, target: State, machine: CatFlapStateMachine
    ):
        if machine.is_locked and not self.lock_engaged:
            _schedule_send(self.loop, self.hub, EngageLockMessage())
            self.lock_engaged = True
        elif self.lock_engaged and not machine.is_locked:
            _schedule_send(self.loop, self.hub, DisengageLockMessage())
            self.lock_engaged = False

    def on_enter_inference(self, source: State):
        if source.id in {"movement_detected", "wait", "locked_and_movement"}:
            _schedule_send(self.loop, self.hub, StartCaptureMessage())


async def handle_messages(hub: WorkerMessageHub, state: CatFlapStateMachine):
    log.info("Starting the logic service")

    state.configure_timers(
        capture_interval.total_seconds(), lockout_duration.total_seconds()
    )

    loop = asyncio.get_running_loop()
    state.add_listener(StateUpdateListener(hub, loop))  # pyright: ignore[reportUnknownMemberType]
    state.add_listener(MessageSenderListener(hub, loop, lock_engaged=state.is_locked))  # pyright: ignore[reportUnknownMemberType]

    if state.movement_detected.is_active:
        state.inference_started()
    elif state.inference.is_active:
        _schedule_send(loop, hub, StartCaptureMessage())

    if (
        state.wait.is_active
        or state.locked.is_active
        or state.locked_and_movement.is_active
        or state.locked_and_door_open.is_active
    ):
        state.restart_timers()

    async for message in hub.receive():
        match message:
            case MotionDetectedMessage():
                if state.is_door_open:
                    log.debug("Ignoring motion while the door is open")
                    continue

                if state.idle.is_active:
                    state.movement()
                    state.inference_started()
                elif state.locked.is_active:
                    state.movement()
                    state.loop_delay_passed()

            case MotionEndedMessage():
                if state.is_movement_detected:
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
                if not (
                    state.inference.is_active or state.inferring_and_door_open.is_active
                ):
                    log.debug("Ignoring inference result with no active inference")
                    continue

                log.info(f"Inference completed, classes detected: {classes}")

                prey_classes = [item for item in classes if item[0] == "prey"]

                if len(prey_classes) > 0:
                    max_prey_prob = max(
                        (prob for _, prob in prey_classes),
                    )

                    if max_prey_prob > prey_lockout_probability:
                        log.info(
                            f"Prey detected with enough probability ({max_prey_prob:.2%} > {prey_lockout_probability:.2%}), locking the flap"
                        )
                        state.prey_detected()
                    else:
                        log.warning(
                            f"Prey detected with not enough probability ({max_prey_prob:.2%} <= {prey_lockout_probability:.2%}), not locking the flap"
                        )
                        state.no_prey()
                else:
                    log.info("No prey detected, not locking the flap")
                    state.no_prey()

            case _:
                pass


if __name__ == "__main__":
    worker_main(log, handle_messages)

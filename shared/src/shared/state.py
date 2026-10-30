from dataclasses import dataclass
from typing import Protocol, cast

from statemachine import State, StateChart
from statemachine.contrib.timeout import timeout
from statemachine.invoke import InvokeContext


class _MachineContext(Protocol):
    machine: object


class _ConfiguredTimeout:
    def __init__(self, duration_attribute: str, event: str):
        self.duration_attribute = duration_attribute
        self.event = event

    def run(self, context: InvokeContext):
        machine = cast(_MachineContext, context).machine
        duration = getattr(machine, self.duration_attribute, None)
        if isinstance(duration, (int, float)):
            return timeout(duration, on=self.event).run(context)


class CatFlapStateMachine(StateChart[object]):
    idle = State(initial=True)
    disabled = State()
    door_open = State()
    movement_detected = State()
    inference = State()
    inferring_and_door_open = State()
    wait = State(
        invoke=_ConfiguredTimeout("capture_interval_seconds", "loop_delay_passed")
    )
    wait_and_door_open = State()
    locked = State(
        invoke=_ConfiguredTimeout("lockout_duration_seconds", "lock_timeout")
    )
    locked_and_movement = State(
        invoke=_ConfiguredTimeout("capture_interval_seconds", "loop_delay_passed")
    )
    locked_and_movement_and_door_open = State()
    locked_and_door_open = State(
        invoke=_ConfiguredTimeout("lockout_duration_seconds", "lock_timeout")
    )

    disable = (
        idle.to(disabled)
        | door_open.to(disabled)
        | movement_detected.to(disabled)
        | inference.to(disabled)
        | inferring_and_door_open.to(disabled)
        | wait.to(disabled)
        | wait_and_door_open.to(disabled)
        | locked.to(disabled)
        | locked_and_movement.to(disabled)
        | locked_and_movement_and_door_open.to(disabled)
        | locked_and_door_open.to(disabled)
    )

    enable = disabled.to(idle)

    door_opened = (
        idle.to(door_open)
        | locked.to(locked_and_door_open)
        | locked_and_movement.to(locked_and_movement_and_door_open)
        | inference.to(inferring_and_door_open)
        | movement_detected.to(door_open)
        | wait.to(wait_and_door_open)
    )

    door_closed = (
        door_open.to(idle)
        | locked_and_movement_and_door_open.to(locked_and_movement)
        | inferring_and_door_open.to(inference)
        | wait_and_door_open.to(wait)
        | locked_and_door_open.to(locked)
    )

    movement = idle.to(movement_detected) | locked.to(locked_and_movement)

    movement_ended = (
        locked_and_movement.to(locked)
        | wait.to(idle)
        | wait_and_door_open.to(door_open)
        | locked_and_movement_and_door_open.to(locked_and_door_open)
        | movement_detected.to(idle)
        | inference.to(idle)
        | inferring_and_door_open.to(door_open)
    )

    inference_started = movement_detected.to(inference)

    inference_ended = inferring_and_door_open.to(door_open)

    prey_detected = inference.to(locked_and_movement) | inferring_and_door_open.to(
        locked_and_movement_and_door_open
    )

    no_prey = inference.to(wait) | inferring_and_door_open.to(wait_and_door_open)

    loop_delay_passed = wait.to(inference) | locked_and_movement.to(inference)

    lock_timeout = locked.to(idle) | locked_and_door_open.to(door_open)

    restart_timers = (
        wait.to(wait)
        | locked.to(locked)
        | locked_and_movement.to(locked_and_movement)
        | locked_and_door_open.to(locked_and_door_open)
    )

    def configure_timers(
        self, capture_interval_seconds: float, lockout_duration_seconds: float
    ):
        if capture_interval_seconds <= 0 or lockout_duration_seconds <= 0:
            raise ValueError("State-machine timeout durations must be positive")

        self.capture_interval_seconds = capture_interval_seconds
        self.lockout_duration_seconds = lockout_duration_seconds

    @property
    def is_door_open(self):
        return (
            self.door_open.is_active
            or self.inferring_and_door_open.is_active
            or self.wait_and_door_open.is_active
            or self.locked_and_door_open.is_active
            or self.locked_and_movement_and_door_open.is_active
        )

    @property
    def is_locked(self):
        return (
            self.locked.is_active
            or self.locked_and_movement.is_active
            or self.locked_and_door_open.is_active
            or self.locked_and_movement_and_door_open.is_active
        )

    @property
    def is_disabled(self):
        return self.disabled.is_active

    @property
    def is_movement_detected(self):
        return (
            self.movement_detected.is_active
            or self.inference.is_active
            or self.inferring_and_door_open.is_active
            or self.wait.is_active
            or self.wait_and_door_open.is_active
            or self.locked_and_movement.is_active
            or self.locked_and_movement_and_door_open.is_active
        )


@dataclass
class StateRef:
    state: CatFlapStateMachine

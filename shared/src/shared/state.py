from dataclasses import dataclass
from statemachine import State, StateChart


class CatFlapStateMachine(StateChart):
    idle = State(initial=True)
    disabled = State()
    door_open = State()
    movement_detected = State()
    inference = State()
    inferring_and_door_open = State()
    wait = State()
    locked = State()
    locked_and_movement = State()
    locked_and_movement_and_door_open = State()
    locked_and_door_open = State()

    disable = (
        idle.to(disabled)
        | door_open.to(disabled)
        | movement_detected.to(disabled)
        | inference.to(disabled)
        | inferring_and_door_open.to(disabled)
        | wait.to(disabled)
        | locked.to(disabled)
        | locked_and_movement.to(disabled)
        | locked_and_movement_and_door_open.to(disabled)
        | locked_and_door_open.to(disabled)
    )

    enable = disabled.to(idle)

    door_opened = (
        idle.to(door_open)
        | locked_and_movement.to(locked_and_movement_and_door_open)
        | inference.to(inferring_and_door_open)
        | movement_detected.to(door_open)
    )

    door_closed = (
        door_open.to(idle)
        | locked_and_movement_and_door_open.to(locked_and_movement)
        | inferring_and_door_open.to(inference)
        | locked_and_door_open.to(locked)
    )

    movement = idle.to(movement_detected)

    movement_ended = (
        locked_and_movement.to(locked)
        | wait.to(idle)
        | locked_and_movement_and_door_open.to(locked_and_door_open)
        | movement_detected.to(idle)
        | inference.to(idle)
    )

    inference_started = movement_detected.to(inference)

    inference_ended = inferring_and_door_open.to(door_open)

    prey_detected = inference.to(locked_and_movement)

    no_prey = inference.to(wait)

    loop_delay_passed = wait.to(inference) | locked_and_movement.to(inference)

    lock_timeout = (
        locked.to(idle)
        | locked_and_door_open.to(door_open)
        | locked_and_movement_and_door_open.to(door_open)
    )

    @property
    def is_door_open(self):
        return (
            self.door_open.is_active
            or self.inferring_and_door_open.is_active
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
            or self.locked_and_movement.is_active
            or self.locked_and_movement_and_door_open.is_active
        )


@dataclass
class StateRef:
    state: CatFlapStateMachine

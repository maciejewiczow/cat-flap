import time

import pytest

from .state import CatFlapStateMachine


@pytest.fixture
def state_machine():
    return CatFlapStateMachine()


def test_initial_state(state_machine: CatFlapStateMachine):
    assert state_machine.current_state == state_machine.idle


def test_disable_from_idle(state_machine: CatFlapStateMachine):
    state_machine.disable()
    assert state_machine.current_state == state_machine.disabled


def test_disable_from_door_open(state_machine: CatFlapStateMachine):
    state_machine.door_opened()
    state_machine.disable()
    assert state_machine.current_state == state_machine.disabled


def test_disable_from_movement_detected(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.disable()
    assert state_machine.current_state == state_machine.disabled


def test_disable_from_inference(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.disable()
    assert state_machine.current_state == state_machine.disabled


def test_disable_from_inferring_and_door_open(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.door_opened()
    state_machine.disable()
    assert state_machine.current_state == state_machine.disabled


def test_disable_from_wait(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.no_prey()
    state_machine.disable()
    assert state_machine.current_state == state_machine.disabled


def test_disable_from_locked(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.disable()
    assert state_machine.current_state == state_machine.disabled


def test_disable_from_locked_and_movement(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.disable()
    assert state_machine.current_state == state_machine.disabled


def test_disable_from_locked_and_movement_and_door_open(
    state_machine: CatFlapStateMachine,
):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.door_opened()
    state_machine.disable()
    assert state_machine.current_state == state_machine.disabled


def test_disable_from_locked_and_door_open(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.door_opened()
    state_machine.door_closed()
    state_machine.disable()
    assert state_machine.current_state == state_machine.disabled


def test_enable_from_disabled(state_machine: CatFlapStateMachine):
    state_machine.disable()
    state_machine.enable()
    assert state_machine.current_state == state_machine.idle


def test_door_opened_from_idle(state_machine: CatFlapStateMachine):
    state_machine.door_opened()
    assert state_machine.current_state == state_machine.door_open


def test_door_opened_from_locked_and_movement(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.door_opened()
    assert (
        state_machine.current_state == state_machine.locked_and_movement_and_door_open
    )


def test_door_opened_from_inference(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.door_opened()
    assert state_machine.current_state == state_machine.inferring_and_door_open


def test_door_opened_from_movement_detected(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.door_opened()
    assert state_machine.current_state == state_machine.door_open


def test_door_closed_from_door_open(state_machine: CatFlapStateMachine):
    state_machine.door_opened()
    state_machine.door_closed()
    assert state_machine.current_state == state_machine.idle


def test_door_closed_from_locked_and_movement_and_door_open(
    state_machine: CatFlapStateMachine,
):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.door_opened()
    state_machine.door_closed()
    assert state_machine.current_state == state_machine.locked_and_movement


def test_door_closed_from_inferring_and_door_open(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.door_opened()
    state_machine.door_closed()
    assert state_machine.current_state == state_machine.inference


def test_door_opened_from_wait(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.no_prey()
    state_machine.door_opened()
    assert state_machine.current_state == state_machine.wait_and_door_open


def test_door_closed_from_wait_and_door_open(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.no_prey()
    state_machine.door_opened()
    state_machine.door_closed()
    assert state_machine.current_state == state_machine.wait


def test_door_closed_from_locked_and_door_open(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.door_opened()
    state_machine.door_closed()
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.door_opened()
    state_machine.movement_ended()
    assert state_machine.current_state == state_machine.locked_and_door_open
    state_machine.door_closed()
    assert state_machine.current_state == state_machine.locked


def test_movement_from_idle(state_machine: CatFlapStateMachine):
    state_machine.movement()
    assert state_machine.current_state == state_machine.movement_detected


def test_motion_resumes_capture_from_locked(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.movement_ended()
    state_machine.movement()
    assert state_machine.current_state == state_machine.locked_and_movement
    state_machine.loop_delay_passed()
    assert state_machine.current_state == state_machine.inference


def test_movement_ended_from_locked_and_movement(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.movement_ended()
    assert state_machine.current_state == state_machine.locked


def test_movement_ended_from_wait(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.no_prey()
    state_machine.movement_ended()
    assert state_machine.current_state == state_machine.idle


def test_movement_ended_from_locked_and_movement_and_door_open(
    state_machine: CatFlapStateMachine,
):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.door_opened()
    state_machine.movement_ended()
    assert state_machine.current_state == state_machine.locked_and_door_open


def test_movement_ended_from_inferring_and_door_open(
    state_machine: CatFlapStateMachine,
):
    state_machine.door_opened()
    state_machine.movement()
    state_machine.movement_ended()
    assert state_machine.current_state == state_machine.door_open


def test_movement_ended_from_movement_detected(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.movement_ended()
    assert state_machine.current_state == state_machine.idle


def test_movement_ended_from_inference(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.movement_ended()
    assert state_machine.current_state == state_machine.idle


def test_inference_started_from_movement_detected(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    assert state_machine.current_state == state_machine.inference


def test_inference_ended_from_inferring_and_door_open(
    state_machine: CatFlapStateMachine,
):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.door_opened()
    state_machine.inference_ended()
    assert state_machine.current_state == state_machine.door_open


def test_prey_detected_from_inference(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    assert state_machine.current_state == state_machine.locked_and_movement


def test_no_prey_from_inference(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.no_prey()
    assert state_machine.current_state == state_machine.wait


def test_loop_delay_passed_from_wait(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.no_prey()
    state_machine.loop_delay_passed()
    assert state_machine.current_state == state_machine.inference


def test_loop_delay_passed_from_locked_and_movement(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.loop_delay_passed()
    assert state_machine.current_state == state_machine.inference


def test_lock_timeout_from_locked(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.movement_ended()
    state_machine.lock_timeout()
    assert state_machine.current_state == state_machine.idle


def test_lock_timeout_from_locked_and_door_open(state_machine: CatFlapStateMachine):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.door_opened()
    state_machine.movement_ended()
    state_machine.lock_timeout()
    assert state_machine.current_state == state_machine.door_open


def test_capture_timeout_returns_to_inference(state_machine: CatFlapStateMachine):
    state_machine.configure_timers(0.03, 1)
    state_machine.movement()
    state_machine.inference_started()
    state_machine.no_prey()

    deadline = time.monotonic() + 1
    while not state_machine.inference.is_active and time.monotonic() < deadline:
        time.sleep(0.01)

    assert state_machine.inference.is_active


def test_capture_timeout_is_cancelled_when_motion_ends(
    state_machine: CatFlapStateMachine,
):
    state_machine.configure_timers(0.1, 1)
    state_machine.movement()
    state_machine.inference_started()
    state_machine.no_prey()
    state_machine.movement_ended()

    time.sleep(0.15)

    assert state_machine.idle.is_active


def test_capture_retry_pauses_while_door_is_open(state_machine: CatFlapStateMachine):
    state_machine.configure_timers(0.03, 1)
    state_machine.movement()
    state_machine.inference_started()
    state_machine.no_prey()
    state_machine.door_opened()

    time.sleep(0.1)

    assert state_machine.wait_and_door_open.is_active


def test_locked_capture_retry_pauses_while_door_is_open(
    state_machine: CatFlapStateMachine,
):
    state_machine.configure_timers(0.03, 1)
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.door_opened()

    time.sleep(0.1)

    assert state_machine.locked_and_movement_and_door_open.is_active


def test_lock_timeout_starts_after_motion_ends(state_machine: CatFlapStateMachine):
    state_machine.configure_timers(1, 0.05)
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()

    time.sleep(0.1)
    assert state_machine.locked_and_movement.is_active

    state_machine.movement_ended()
    deadline = time.monotonic() + 1
    while not state_machine.idle.is_active and time.monotonic() < deadline:
        time.sleep(0.01)

    assert state_machine.idle.is_active


def test_lock_timeout_keeps_door_open(state_machine: CatFlapStateMachine):
    state_machine.configure_timers(1, 0.05)
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.door_opened()
    state_machine.movement_ended()

    deadline = time.monotonic() + 1
    while not state_machine.door_open.is_active and time.monotonic() < deadline:
        time.sleep(0.01)

    assert state_machine.door_open.is_active


def test_restart_timers_starts_capture_timeout_after_restore(
    state_machine: CatFlapStateMachine,
):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.no_prey()
    state_machine.configure_timers(0.03, 1)
    state_machine.restart_timers()

    deadline = time.monotonic() + 1
    while not state_machine.inference.is_active and time.monotonic() < deadline:
        time.sleep(0.01)

    assert state_machine.inference.is_active


def test_restart_timers_starts_lock_timeout_after_restore(
    state_machine: CatFlapStateMachine,
):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.movement_ended()
    state_machine.configure_timers(1, 0.03)
    state_machine.restart_timers()

    deadline = time.monotonic() + 1
    while not state_machine.idle.is_active and time.monotonic() < deadline:
        time.sleep(0.01)

    assert state_machine.idle.is_active


def test_lock_timeout_does_not_transition_while_moving(
    state_machine: CatFlapStateMachine,
):
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.door_opened()
    state_machine.lock_timeout()
    assert (
        state_machine.current_state == state_machine.locked_and_movement_and_door_open
    )


def test_is_door_open_property(state_machine: CatFlapStateMachine):
    assert not state_machine.is_door_open
    state_machine.door_opened()
    assert state_machine.is_door_open
    state_machine.movement()
    state_machine.inference_started()
    state_machine.door_opened()
    assert state_machine.is_door_open
    state_machine.movement()
    state_machine.inference_started()
    state_machine.prey_detected()
    state_machine.door_opened()
    assert state_machine.is_door_open
    state_machine.movement_ended()
    assert state_machine.is_door_open
    state_machine.door_closed()
    assert not state_machine.is_door_open

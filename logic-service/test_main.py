import asyncio
from collections.abc import Callable
from os import environ
from tempfile import gettempdir
from typing import cast

environ.setdefault("LOG_FOLDER", f"{gettempdir()}/cat-flap-test-logs")

from main import MessageSenderListener, handle_messages
from shared.hub import WorkerMessageHub
from shared.messages import (
    DisengageLockMessage,
    EngageLockMessage,
    Message,
    MotionDetectedMessage,
    StartCaptureMessage,
)
from shared.state import CatFlapStateMachine


class _RecordingHub:
    def __init__(self, incoming: list[Message] | None = None):
        self.messages: list[Message] = []
        self.incoming = incoming or []

    async def send(self, message: Message):
        self.messages.append(message)

    async def receive(self):
        for message in self.incoming:
            yield message


def test_motion_while_door_open_does_not_start_capture():
    async def run_scenario():
        recording_hub = _RecordingHub([MotionDetectedMessage()])
        state = CatFlapStateMachine()
        state.door_opened()

        await handle_messages(cast(WorkerMessageHub, recording_hub), state)

        assert state.door_open.is_active
        assert not any(
            isinstance(message, StartCaptureMessage)
            for message in recording_hub.messages
        )

    asyncio.run(run_scenario())


def test_capture_repeats_until_motion_ends_and_lock_times_out():
    async def run_scenario():
        recording_hub = _RecordingHub()
        hub = cast(WorkerMessageHub, recording_hub)
        state = CatFlapStateMachine()
        state.configure_timers(0.02, 0.04)
        listener = MessageSenderListener(hub, asyncio.get_running_loop())
        state.add_listener(listener)

        async def wait_for(predicate: Callable[[], bool]):
            deadline = asyncio.get_running_loop().time() + 1
            while not predicate() and asyncio.get_running_loop().time() < deadline:
                await asyncio.sleep(0.005)
            assert predicate()

        state.movement()
        state.inference_started()
        await wait_for(
            lambda: (
                sum(
                    isinstance(message, StartCaptureMessage)
                    for message in recording_hub.messages
                )
                == 1
            )
        )

        state.no_prey()
        await wait_for(
            lambda: (
                sum(
                    isinstance(message, StartCaptureMessage)
                    for message in recording_hub.messages
                )
                == 2
            )
        )

        state.prey_detected()
        await wait_for(
            lambda: (
                sum(
                    isinstance(message, EngageLockMessage)
                    for message in recording_hub.messages
                )
                == 1
            )
        )
        await wait_for(
            lambda: (
                sum(
                    isinstance(message, StartCaptureMessage)
                    for message in recording_hub.messages
                )
                == 3
            )
        )

        state.prey_detected()
        state.movement_ended()
        await wait_for(
            lambda: (
                sum(
                    isinstance(message, DisengageLockMessage)
                    for message in recording_hub.messages
                )
                == 1
            )
        )

    asyncio.run(run_scenario())

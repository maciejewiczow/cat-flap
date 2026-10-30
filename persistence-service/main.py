import asyncio
from collections.abc import MutableSet
from pathlib import Path

from pydantic import BaseModel, ValidationError
from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.main_fn import persistence_worker_main
from shared.messages import ServiceActivated, StateUpdate
from shared.state import CatFlapStateMachine

log = get_logger("persistence-service")
state_file = Path("/data/state.json")


class StateMachineSnapshot(BaseModel):
    current_state: str | MutableSet[str]


def read_snapshot():
    if not state_file.exists():
        log.error("State file does not exist. Cannot restore state.")
        raise FileNotFoundError("State file does not exist.")

    snapshot = StateMachineSnapshot.model_validate_json(
        state_file.read_text(encoding="utf-8")
    )

    return snapshot


def write_snapshot(state_machine: CatFlapStateMachine):
    state_file.write_text(
        StateMachineSnapshot(
            current_state=state_machine.current_state.id
            if not isinstance(state_machine.current_state, MutableSet)
            else {state.id for state in state_machine.current_state}
        ).model_dump_json(),
        encoding="utf-8",
    )


async def handle_messages(hub: WorkerMessageHub):
    log.info("Starting the persistence service")

    async for message in hub.receive():
        match message:
            case StateUpdate(new_state=state_machine):
                log.info("Got state from the logic svc")
                await asyncio.to_thread(write_snapshot, state_machine)

            case ServiceActivated():
                try:
                    if not state_file.exists():
                        log.error("State file does not exist. Cannot restore state.")
                        raise FileNotFoundError("State file does not exist.")

                    snapshot = await asyncio.to_thread(read_snapshot)

                    state_machine = CatFlapStateMachine()

                    state_machine.current_state_value = snapshot.current_state

                    await hub.send(StateUpdate(new_state=state_machine))
                except ValidationError as e:
                    log.error(f"Error occurred while validating state file: {e}")
                    await hub.send(StateUpdate(new_state=CatFlapStateMachine()))
                except FileNotFoundError as e:
                    log.error(f"Error occurred while reading state file: {e}")
                    await hub.send(StateUpdate(new_state=CatFlapStateMachine()))

            case _:
                pass


if __name__ == "__main__":
    persistence_worker_main(log, handle_messages)

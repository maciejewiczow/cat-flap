from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.main_fn import persistence_worker_main, worker_main
from shared.messages import MotionDetectedMessage, StateUpdate
from shared.state import State, StateRef, SystemState, update_state

log = get_logger("persistence-service")


async def handle_messages(hub: WorkerMessageHub):
    log.info("Starting the persistence service")

    state = State()

    async for message in hub.receive():
        match message:
            case MotionDetectedMessage():
                state.state = SystemState.movement_detected
                await hub.send(StateUpdate(new_state=state))


if __name__ == "__main__":
    persistence_worker_main(log, handle_messages)

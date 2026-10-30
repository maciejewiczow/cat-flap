import asyncio
import signal
import time
from collections.abc import Callable, Coroutine
from logging import Logger
from os import environ
from typing import Any

from shared.messages import ServiceActivated, StateUpdate
from shared.state import CatFlapStateMachine

from .hub import WorkerMessageHub


def get_hub(log: Logger):
    return WorkerMessageHub(environ["SOCKETS_DIR"], log)


def setup_signal_handlers(log: Logger):
    def signal_handler(signum: Any, frame: Any):
        log.info(f"Signal {signum} received, shutting down...")
        asyncio.get_event_loop().stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def persistence_worker_main(
    log: Logger,
    message_handler: Callable[[WorkerMessageHub], Coroutine[Any, Any, None]],
):
    time.sleep(1)
    try:
        hub = get_hub(log)

        setup_signal_handlers(log)

        asyncio.run(message_handler(hub))
    except KeyError:
        log.exception("Missing socket dir config")


def worker_main(
    log: Logger,
    message_handler: Callable[
        [WorkerMessageHub, CatFlapStateMachine], Coroutine[Any, Any, None]
    ],
):
    try:
        hub = get_hub(log)

        setup_signal_handlers(log)

        async def main(hub: WorkerMessageHub):
            log.info("Sending service activated message")
            await hub.send(ServiceActivated())

            log.info("Waiting for response")
            async for message in hub.receive():
                match message:
                    case StateUpdate(new_state=state):
                        log.info("Got state from the persistence svc")
                        break
                    case _:
                        pass

            await message_handler(hub, state)  # pyright: ignore[reportPossiblyUnboundVariable]

        asyncio.run(main(hub))
    except KeyError:
        log.exception("Missing socket dir config")

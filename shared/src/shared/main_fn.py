import asyncio
from logging import Logger
from os import environ
import signal
from typing import Any, Callable, Coroutine
from .hub import WorkerMessageHub


def worker_main(
    log: Logger,
    message_handler: Callable[[WorkerMessageHub], Coroutine[Any, Any, None]],
):
    try:
        loop = asyncio.get_event_loop()

        hub = WorkerMessageHub(environ["SOCKETS_DIR"])

        def signal_handler(signum, frame):
            log.info(f"Signal {signum} received, shutting down...")
            loop.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        loop.run_until_complete(message_handler(hub))
    except KeyError:
        log.exception("Missing socket dir config")

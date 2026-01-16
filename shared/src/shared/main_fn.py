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
        hub = WorkerMessageHub(environ["SOCKETS_DIR"])

        def signal_handler(signum, frame):
            log.info(f"Signal {signum} received, shutting down...")
            asyncio.get_event_loop().stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        asyncio.run(message_handler(hub))
    except KeyError:
        log.exception("Missing socket dir config")

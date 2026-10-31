from os import environ

from gpiozero import DigitalOutputDevice
from gpiozero.pins.pigpio import PiGPIOFactory
from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.main_fn import worker_main
from shared.messages import DisengageLockMessage, EngageLockMessage
from shared.state import CatFlapStateMachine

log = get_logger("lock-service")

pin_factory = PiGPIOFactory(
    host=environ.get("PIGPIO_ADDR", "localhost"),
    port=environ.get("PIGPIO_PORT", "8888"),
)

lock_electromagnet = DigitalOutputDevice(
    int(environ["LOCK_PIN"]),
    pin_factory=pin_factory,
    active_high=False,
    initial_value=False,
)


async def handle_messages(hub: WorkerMessageHub, initial_state: CatFlapStateMachine):
    log.info("Starting the Service managing the locking and unlocking of the flap")

    if initial_state.is_locked:
        lock_electromagnet.on()

    async for message in hub.receive():
        match message:
            case EngageLockMessage():
                log.info("Engaging lock")
                lock_electromagnet.on()

            case DisengageLockMessage():
                log.info("Disengaging lock")
                lock_electromagnet.off()

            case _:
                pass


if __name__ == "__main__":
    worker_main(log, handle_messages)

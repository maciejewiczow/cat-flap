from os import environ
from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.messages import (
    LockFlapMessage,
    UnlockFlapMessage,
)
from shared.main_fn import worker_main
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory

log = get_logger("servo")

factory = PiGPIOFactory()

servo = Servo(
    int(environ.get("SERVO_PIN", 12)),
    min_pulse_width=0.5 / 1000,
    max_pulse_width=2.5 / 1000,
    pin_factory=factory,
)


async def handle_messages(hub: WorkerMessageHub):
    log.info("Starting the servo service")

    async for message in hub.receive():
        match message:
            case LockFlapMessage():
                log.info("Initiating flap locking")
                servo.value = -1.0
            case UnlockFlapMessage():
                log.info("Initiating flap unlocking")
                servo.value = 1.0


if __name__ == "__main__":
    worker_main(log, handle_messages)

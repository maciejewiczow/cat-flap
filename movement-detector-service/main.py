import asyncio
from concurrent.futures import ThreadPoolExecutor
from os import environ
from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.main_fn import worker_main
from gpiozero import Button
from gpiozero.pins.pigpio import PiGPIOFactory
from shared.messages import MotionDetectedMessage, MotionEndedMessage

log = get_logger("movement-detector")

executor = ThreadPoolExecutor(max_workers=1)

factory = PiGPIOFactory()

button = Button(pin=int(environ.get("MOTION_SENSOR_PIN", 25)), pin_factory=factory)


async def handle_messages(hub: WorkerMessageHub):
    log.info("Starting the movement detector service")
    loop = asyncio.get_event_loop()

    while True:
        await loop.run_in_executor(executor, button.wait_for_active)
        log.info("Movement detected, sending a message")
        await hub.send(MotionDetectedMessage())
        await loop.run_in_executor(executor, button.wait_for_inactive)
        log.info("Movement ended, sending an end message")
        await hub.send(MotionEndedMessage())


if __name__ == "__main__":
    worker_main(log, handle_messages)

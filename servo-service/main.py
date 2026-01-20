import asyncio
from os import environ
from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.messages import (
    FlapInTransitionMessage,
    FlapLockedMessage,
    FlapUnlockedMessage,
    LockFlapMessage,
    UnlockFlapMessage,
)
from shared.main_fn import worker_main
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

log = get_logger("servo")

factory = PiGPIOFactory()

servo = Servo(
    int(environ.get("SERVO_PIN", 12)),
    min_pulse_width=0.5 / 1000,
    max_pulse_width=2.5 / 1000,
    pin_factory=factory,
)

spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

cs = digitalio.DigitalInOut(board.D5)

mcp = MCP.MCP3008(spi, cs)

chan = AnalogIn(mcp, MCP.P0)


async def wait_for_unlock(hub: WorkerMessageHub):
    try:
        while chan.voltage > 0.01:
            await asyncio.sleep(0.1)

        await hub.send(FlapUnlockedMessage())
    except asyncio.CancelledError:
        return


async def wait_for_lock(hub: WorkerMessageHub):
    try:
        while chan.voltage < 3.2:
            await asyncio.sleep(0.1)

        await hub.send(FlapLockedMessage())
    except asyncio.CancelledError:
        return


async def handle_messages(hub: WorkerMessageHub):
    log.info("Starting the servo service")
    servo.max()
    log.info("Initially unlocked the flap")

    loop = asyncio.get_event_loop()

    wait_for_lock_task: asyncio.Task[None] | None = None
    wait_for_unlock_task: asyncio.Task[None] | None = None

    async for message in hub.receive():
        match message:
            case LockFlapMessage():
                log.info("Initiating flap locking")
                await hub.send(FlapInTransitionMessage())
                servo.min()

                if wait_for_lock_task is None or wait_for_lock_task.done():
                    if wait_for_unlock_task is not None:
                        wait_for_unlock_task.cancel()
                        log.info("Cancelled pending flap unlock")
                        wait_for_unlock_task = None

                    wait_for_lock_task = loop.create_task(wait_for_lock(hub))

            case UnlockFlapMessage():
                log.info("Initiating flap unlocking")
                await hub.send(FlapInTransitionMessage())
                servo.max()

                if wait_for_unlock_task is None or wait_for_unlock_task.done():
                    if wait_for_lock_task is not None:
                        wait_for_lock_task.cancel()
                        log.info("Cancelled pending flap lock")
                        wait_for_lock_task = None

                    wait_for_unlock_task = loop.create_task(wait_for_unlock(hub))


if __name__ == "__main__":
    worker_main(log, handle_messages)

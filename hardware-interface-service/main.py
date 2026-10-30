import asyncio
from os import environ

from gpiozero import Button, Buzzer
from gpiozero.pins.pigpio import PiGPIOFactory
from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.main_fn import worker_main
from shared.messages import (
    DoorClosedMessage,
    DoorOpenedMessage,
    EngageLockMessage,
    MainButtonPressedMessage,
    StateUpdate,
)
from shared.state import CatFlapStateMachine
from smbus3 import SMBus
from src.Expander import Expander

pin_factory = PiGPIOFactory(
    host=environ.get("PIGPIO_ADDR", "localhost"),
    port=environ.get("PIGPIO_PORT", "8888"),
)

log = get_logger("hardware-interface")

bus = SMBus(int(environ.get("I2C_BUS_NUMBER", "1")))

expander = Expander(bus, address=int(environ.get("I2C_EXPANDER_ADDRESS", "0x20"), 16))

active_diode = expander.pin(int(environ["ACTIVE_DIODE_EXPANDER_PIN"]))
movement_detected_diode = expander.pin(
    int(environ["MOTION_DETECTED_DIODE_EXPANDER_PIN"])
)
locked_diode = expander.pin(int(environ["LOCKED_DIODE_EXPANDER_PIN"]))
door_open_diode = expander.pin(int(environ["DOOR_OPEN_DIODE_EXPANDER_PIN"]))
inference_diode = expander.pin(int(environ["INFERENCE_DIODE_EXPANDER_PIN"]))

door_open_detector = Button(
    int(environ["DOOR_SENSOR_PIN"]), pull_up=False, pin_factory=pin_factory
)

buzzer = Buzzer(int(environ["BUZZER_PIN"]), pin_factory=pin_factory)

mode_switch_button = Button(int(environ["MODE_BUTTON_PIN"]), pin_factory=pin_factory)


async def sound_buzzer_short():
    buzzer.on()
    await asyncio.sleep(0.2)
    buzzer.off()


async def sound_buzzer_alarm():
    buzzer.on()
    await asyncio.sleep(0.5)
    buzzer.off()
    await asyncio.sleep(0.5)

    buzzer.on()
    await asyncio.sleep(0.5)
    buzzer.off()
    await asyncio.sleep(0.5)

    buzzer.on()
    await asyncio.sleep(1)
    buzzer.off()


def update_diodes(state: CatFlapStateMachine):
    if state.is_locked:
        locked_diode.on()
    else:
        locked_diode.off()

    if state.is_door_open:
        door_open_diode.on()
    else:
        door_open_diode.off()

    if state.is_movement_detected:
        movement_detected_diode.on()
    else:
        movement_detected_diode.off()

    if state.is_disabled:
        active_diode.off()
    else:
        active_diode.on()

    if state.is_inferring:
        inference_diode.on()
    else:
        inference_diode.off()


async def handle_messages(hub: WorkerMessageHub, initial_state: CatFlapStateMachine):
    log.info("Starting the hardware service")

    door_open_detector.when_pressed = lambda: asyncio.create_task(
        hub.send(DoorOpenedMessage())
    )
    door_open_detector.when_released = lambda: asyncio.create_task(
        hub.send(DoorClosedMessage())
    )

    mode_switch_button.when_pressed = lambda: asyncio.create_task(
        hub.send(MainButtonPressedMessage())
    )

    update_diodes(initial_state)

    async for message in hub.receive():
        match message:
            case StateUpdate(new_state=state):
                update_diodes(state)

            case EngageLockMessage():
                log.info("Lock engaged, sounding alarm")
                asyncio.create_task(sound_buzzer_alarm())

            case MainButtonPressedMessage():
                asyncio.create_task(sound_buzzer_short())

            case _:
                pass


if __name__ == "__main__":
    worker_main(log, handle_messages)

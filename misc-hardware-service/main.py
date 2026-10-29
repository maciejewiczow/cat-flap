from os import environ
from smbus3 import SMBus
from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.messages import ImageCapturedMessage, InferenceCompleteMessage
from shared.main_fn import worker_main
from src.Expander import Expander
from gpiozero import Button, Buzzer, DigitalOutputDevice
from gpiozero.pins.pigpio import PiGPIOFactory

pin_factory = PiGPIOFactory(
    host=environ.get("PIGPIO_ADDR", "localhost"),
    port=environ.get("PIGPIO_PORT", "8888"),
)

log = get_logger("hardware")

bus = SMBus(int(environ.get("I2C_BUS_NUMBER", 1)))

expander = Expander(bus, address=int(environ.get("I2C_EXPANDER_ADDRESS", 0x20)))

acitve_diode = expander.pin(int(environ["ACTIVE_DIODE_PIN"]))
motion_detected_diode = expander.pin(int(environ["MOTION_DETECTED_DIODE_PIN"]))
locked_diode = expander.pin(int(environ["LOCKED_DIODE_PIN"]))
door_open_diode = expander.pin(int(environ["DOOR_OPEN_DIODE_PIN"]))

door_open_detector = Button(
    int(environ["DOOR_SENSOR_PIN"]), pull_up=False, pin_factory=pin_factory
)

buzzer = Buzzer(int(environ["BUZZER_PIN"]), pin_factory=pin_factory)

lock_electromagnet = DigitalOutputDevice(
    int(environ["LOCK_PIN"]), pin_factory=pin_factory
)

mode_switch_button = Button(int(environ["MODE_BUTTON_PIN"]), pin_factory=pin_factory)


async def handle_messages(hub: WorkerMessageHub):
    log.info("Starting the hardware service")

    async for message in hub.receive():
        match message:
            case ImageCapturedMessage():
                pass
            case InferenceCompleteMessage():
                pass


if __name__ == "__main__":
    worker_main(log, handle_messages)

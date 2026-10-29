from typing import Callable
from smbus3 import SMBus

IODIRA_REGISTER = 0x0
IODIRB_REGISTER = 0x1

OLATA_REGISTER = 0x14
OLATB_REGISTER = 0x15


class Pin:
    def __init__(self, e: "Expander", nr: int) -> None:
        self.expander = e
        self.nr = nr

    def on(self):
        self.expander._pin_on(self)

    def off(self):
        self.expander._pin_off(self)

    def toggle(self):
        self.expander._pin_toggle(self)


class Expander:
    def __init__(self, bus: SMBus, *, address: int) -> None:
        self.bus = bus
        self.addr = address
        self.register_a_state = 0x0
        self.register_b_state = 0x0

        self.bus.write_byte_data(self.addr, IODIRA_REGISTER, 0x0)
        self.bus.write_byte_data(self.addr, IODIRB_REGISTER, 0x0)

    def _pin_on(self, pin: Pin):
        self._modify_register(
            pin.nr, lambda reg, nr: self._apply_state_change(reg, nr, True)
        )

    def _pin_off(self, pin: Pin):
        self._modify_register(
            pin.nr, lambda reg, nr: self._apply_state_change(reg, nr, False)
        )

    def _pin_toggle(self, pin: Pin):
        self._modify_register(pin.nr, self._apply_toggle)

    def _modify_register(self, pin_no: int, action: Callable[[int, int], int]):
        if pin_no > 7:
            self.register_b_state = action(self.register_b_state, pin_no - 8)
            self.bus.write_byte_data(self.addr, OLATB_REGISTER, self.register_b_state)
        else:
            self.register_a_state = action(self.register_b_state, pin_no)
            self.bus.write_byte_data(self.addr, OLATA_REGISTER, self.register_a_state)

    @staticmethod
    def _apply_toggle(reg: int, pin_no: int):
        return reg ^ (0x1 << pin_no)

    @staticmethod
    def _apply_state_change(reg: int, pin_no: int, state: bool):
        mask = 1 << pin_no

        if state:
            return reg | mask

        return reg & ~mask

    def pin(self, pin_number: int) -> Pin:
        if 0 > pin_number or pin_number > 15:
            raise ValueError("Invalid pin number")

        return Pin(self, pin_number)

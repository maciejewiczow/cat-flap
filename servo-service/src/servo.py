from gpiozero import Servo


class FT90RServo(Servo):
    def __init__(
        self,
        pin=None,
        *,
        pin_factory=None,
    ):
        super().__init__(
            pin,
            initial_value=0,
            min_pulse_width=0.9 / 1000,
            max_pulse_width=2.1 / 1000,
            pin_factory=pin_factory,
        )

    def clockwise(self):
        self.value = -1

    def counter_clockwise(self):
        self.value = 1

    def stop(self):
        self.value = 0

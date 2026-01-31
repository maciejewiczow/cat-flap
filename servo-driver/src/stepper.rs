use embassy_rp::gpio::Output;
use embassy_time::Timer;

use crate::utils::interpolate;

#[derive(Debug, Clone, Copy)]
pub enum StepMode {
    /// Full step mode (4 steps per cycle for 4-wire)
    FullStep,
    /// Half step mode (8 steps per cycle for 4-wire)
    HalfStep,
}

#[derive(Debug, Clone, Copy)]
enum Direction {
    Clockwise,
    Counterclockwise,
}

pub struct Stepper<'a> {
    step_mode: StepMode,
    target: u64,
    direction: Direction,
    step_delay: u64, // microseconds between steps
    number_of_steps: u64,
    step_number: u64,
    pin1: Output<'a>,
    pin2: Output<'a>,
    pin3: Output<'a>,
    pin4: Output<'a>,
}

impl<'a> Stepper<'a> {
    pub fn new_four_wire(
        number_of_steps: u64,
        pin1: Output<'a>,
        pin2: Output<'a>,
        pin3: Output<'a>,
        pin4: Output<'a>,
        mode: StepMode,
    ) -> Self {
        Stepper {
            step_mode: mode,
            target: 0,
            direction: Direction::Clockwise,
            step_delay: 0,
            number_of_steps: match mode {
                StepMode::HalfStep => number_of_steps * 2,
                StepMode::FullStep => number_of_steps,
            },
            step_number: 0,
            pin1,
            pin2,
            pin3,
            pin4,
        }
    }
}

impl<'a> Stepper<'a> {
    /// Sets the speed in revolutions per minute (RPM)
    pub fn set_speed(&mut self, speed_rpm: u16) {
        if speed_rpm != 0 {
            // Calculate delay in microseconds: 60 seconds * 1,000,000 microseconds /
            // (steps per revolution * RPM)
            self.step_delay = 60_000_000 / (self.number_of_steps * speed_rpm as u64);
        }
    }

    pub fn is_running(&self) -> bool {
        self.target != self.step_number
    }

    pub fn set_target(&mut self, target: u64) {
        self.direction = if target > self.target {
            Direction::Clockwise
        } else {
            Direction::Counterclockwise
        };

        self.target = target;
    }

    pub fn set_target_deg(&mut self, target: f32) {
        self.set_target(interpolate(target, (0., 360.), (0., self.number_of_steps as f32)) as u64);
    }

    pub async fn run(&mut self) {
        while self.is_running() {
            self.run_step();
            Timer::after_micros(self.step_delay).await;
        }

        self.reset_pins();
    }

    // pub async fn run_cb<TFunc: FnMut() -> bool>(&mut self, mut step_callback: TFunc) {
    //     let mut should_continue = true;
    //     while self.is_running() && should_continue {
    //         self.run_step();
    //         should_continue = step_callback();
    //         Timer::after_micros(self.step_delay).await;
    //     }

    //     self.reset_pins();
    // }

    pub fn stop(&mut self) {
        self.target = self.step_number;
        self.reset_pins();
    }

    fn run_step(&mut self) {
        match self.direction {
            Direction::Clockwise => {
                self.step_number += 1;
                if self.step_number >= self.number_of_steps {
                    self.step_number = 0;
                }
            }
            Direction::Counterclockwise => {
                if self.step_number == 0 {
                    self.step_number = self.number_of_steps;
                }
                self.step_number -= 1;
            }
        }

        self.step_motor();
    }

    pub fn reset_pins(&mut self) {
        self.pin1.set_low();
        self.pin2.set_low();
        self.pin3.set_low();
        self.pin4.set_low();
    }

    fn step_motor(&mut self) {
        match self.step_mode {
            StepMode::FullStep => {
                self.step_motor_four_wire_full_step();
            }
            StepMode::HalfStep => {
                self.step_motor_four_wire_half_step();
            }
        }
    }

    fn step_motor_four_wire_full_step(&mut self) {
        let step_pattern = self.step_number % 4;

        match step_pattern {
            0 => {
                self.pin1.set_high();
                self.pin2.set_low();
                self.pin3.set_low();
                self.pin4.set_high();
            }
            1 => {
                self.pin1.set_high();
                self.pin2.set_high();
                self.pin3.set_low();
                self.pin4.set_low();
            }
            2 => {
                self.pin1.set_low();
                self.pin2.set_high();
                self.pin3.set_high();
                self.pin4.set_low();
            }
            3 => {
                self.pin1.set_low();
                self.pin2.set_low();
                self.pin3.set_high();
                self.pin4.set_high();
            }
            _ => unreachable!(),
        }
    }

    fn step_motor_four_wire_half_step(&mut self) {
        let step_pattern = self.step_number % 8;

        match step_pattern {
            0 => {
                self.pin1.set_high();
                self.pin2.set_low();
                self.pin3.set_low();
                self.pin4.set_high();
            }
            1 => {
                self.pin1.set_high();
                self.pin2.set_low();
                self.pin3.set_low();
                self.pin4.set_low();
            }
            2 => {
                self.pin1.set_high();
                self.pin2.set_high();
                self.pin3.set_low();
                self.pin4.set_low();
            }
            3 => {
                self.pin1.set_low();
                self.pin2.set_high();
                self.pin3.set_low();
                self.pin4.set_low();
            }
            4 => {
                self.pin1.set_low();
                self.pin2.set_high();
                self.pin3.set_high();
                self.pin4.set_low();
            }
            5 => {
                self.pin1.set_low();
                self.pin2.set_low();
                self.pin3.set_high();
                self.pin4.set_low();
            }
            6 => {
                self.pin1.set_low();
                self.pin2.set_low();
                self.pin3.set_high();
                self.pin4.set_high();
            }
            7 => {
                self.pin1.set_low();
                self.pin2.set_low();
                self.pin3.set_low();
                self.pin4.set_high();
            }
            _ => unreachable!(),
        }
    }
}

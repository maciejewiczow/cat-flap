use embassy_rp::gpio::Output;
use embassy_time::{Duration, Timer};
use portable_atomic::{AtomicU16, Ordering};

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

pub const ADC_MIN_VALUE: u16 = 30;
pub const ADC_MAX_VALUE: u16 = 4095;

pub const MIN_DEG_VALUE: f32 = 0.;
pub const MAX_DEG_VALUE: f32 = 270.;

pub struct Stepper<'a> {
    step_mode: StepMode,
    target: u16,
    direction: Direction,
    step_delay: u64, // microseconds between steps
    number_of_steps: u16,
    step_number: u16,
    pin1: Output<'a>,
    pin2: Output<'a>,
    pin3: Output<'a>,
    pin4: Output<'a>,
    adc_value: &'a AtomicU16,
}

impl<'a> Stepper<'a> {
    pub fn new_four_wire(
        number_of_steps: u16,
        pin1: Output<'a>,
        pin2: Output<'a>,
        pin3: Output<'a>,
        pin4: Output<'a>,
        mode: StepMode,
        adc_value: &'a AtomicU16,
    ) -> Self {
        let mut s = Stepper {
            step_mode: mode,
            target: 0,
            direction: Direction::Clockwise,
            step_delay: 10,
            number_of_steps: match mode {
                StepMode::HalfStep => number_of_steps * 2,
                StepMode::FullStep => number_of_steps,
            },
            step_number: 0,
            pin1,
            pin2,
            pin3,
            pin4,
            adc_value,
        };

        s.step_number = interpolate(
            s.get_adc_value() as f32,
            (ADC_MIN_VALUE as f32, ADC_MAX_VALUE as f32),
            (0., s.get_adjusted_number_of_steps() as f32),
        ) as u16;

        s
    }
}

impl<'a> Stepper<'a> {
    /// Sets the speed in revolutions per minute (RPM)
    pub fn set_speed(&mut self, speed_rpm: u16) {
        if speed_rpm > 0 {
            // Calculate delay in microseconds: 60 seconds * 1,000,000 microseconds /
            // (steps per revolution * RPM)
            self.step_delay = 60_000_000 / ((self.number_of_steps * speed_rpm) as u64);
        }
    }

    pub fn is_running(&mut self) -> bool {
        self.target.abs_diff(self.get_adc_value()) > 15
    }

    fn get_adjusted_number_of_steps(&self) -> u16 {
        match self.step_mode {
            StepMode::HalfStep => self.number_of_steps / 2,
            StepMode::FullStep => self.number_of_steps,
        }
    }

    pub fn set_target(&mut self, new_target: u16) {
        let val = interpolate(
            new_target as f32,
            (0., self.get_adjusted_number_of_steps() as f32),
            (ADC_MIN_VALUE as f32, ADC_MAX_VALUE as f32),
        ) as u16;

        self.direction = if val > self.target {
            Direction::Clockwise
        } else {
            Direction::Counterclockwise
        };

        self.target = val;
    }

    pub fn set_target_deg(&mut self, target: f32) {
        self.set_target(interpolate(
            target,
            (MIN_DEG_VALUE, MAX_DEG_VALUE),
            (0., self.get_adjusted_number_of_steps() as f32),
        ) as u16);
    }

    fn get_adc_value(&mut self) -> u16 {
        self.adc_value.load(Ordering::Relaxed)
    }

    pub async fn run(&mut self) {
        while self.is_running() {
            self.run_step();

            Timer::after(Duration::from_micros(self.step_delay)).await;
        }

        self.reset_pins();
    }

    pub async fn stop(&mut self) {
        self.target = self.get_adc_value();
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

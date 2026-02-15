#![no_std]
#![no_main]

mod stepper;
mod utils;

use defmt::Debug2Format;

use crate::{
    stepper::{ADC_MAX_VALUE, ADC_MIN_VALUE, MAX_DEG_VALUE, MIN_DEG_VALUE},
    utils::interpolate,
};
use assign_resources::assign_resources;
use defmt::*;
use embassy_executor::{Executor, Spawner};
use embassy_futures::select::{Either3, select3};
#[allow(unused_imports)]
use embassy_rp::peripherals::{
    self, ADC, I2C1, PIN_2, PIN_3, PIN_6, PIN_7, PIN_10, PIN_11, PIN_28,
};
use embassy_rp::{
    Peri, adc,
    gpio::{Level, Output, Pull},
    multicore::{Stack, spawn_core1},
};
use embassy_rp::{bind_interrupts, i2c, i2c_slave};
use embassy_sync::{
    blocking_mutex::raw::ThreadModeRawMutex,
    channel::{Channel, Receiver, Sender},
    mutex::Mutex,
    signal,
};
use embassy_time::Timer;
use portable_atomic::{AtomicU8, AtomicU16, Ordering};
use static_cell::StaticCell;
use stepper::{StepMode, Stepper};
use zerocopy::TryFromBytes;

use {defmt_rtt as _, panic_probe as _};

type RawMutexUsed = ThreadModeRawMutex;

bind_interrupts!(struct Irqs {
    I2C1_IRQ => i2c::InterruptHandler<I2C1>;
    ADC_IRQ_FIFO => adc::InterruptHandler;
});

const DEV_ADDR: u16 = 0x42;

assign_resources! {
    stepper: StepperResources {
        pin1: PIN_6,
        pin2: PIN_7,
        pin3: PIN_10,
        pin4: PIN_11,
    },
    adc_writer: AdcResources {
        adc: ADC,
        adc_pin: PIN_28,
    },
    i2c: I2CResources {
        i2c1: I2C1,
        sda: PIN_2,
        scl: PIN_3,
    }
}

#[derive(TryFromBytes)]
#[repr(C)]
struct RunToDegArgs {
    deg: f32,
    timeout: u64,
}

#[derive(TryFromBytes)]
#[repr(C)]
struct RunToStepArgs {
    step: u16,
    timeout: u64,
}

#[derive(TryFromBytes)]
struct SetSpeedArgs {
    speed: u16,
}

#[allow(dead_code)]
#[derive(TryFromBytes)]
#[repr(u8)]
enum I2CCommand {
    SetSpeed = 0x1,
    Run = 0x2,
    Stop = 0x3,
    RunToStep = 0x4,
}

enum Command {
    Stop,
    SetSpeed(u16),
    RunToDeg(RunToDegArgs),
    RunToStep(RunToStepArgs),
}

const CHANNEL_BUFFER_SIZE: usize = 20;

const ERROR_INVALID_COMMAND: u8 = 0b10;
const ERROR_SERVO_STUCK: u8 = 0b01;

/// Error bits
/// bit 0 - servo stuck - ex. 0b01
/// bit 1 - invalid command - ex. 0b10
static ERROR_VALUE: AtomicU8 = AtomicU8::new(0);

const STEPPER_STATUS_BIT: u8 = 0b01;

/// Stepper status
static STEPPER_STATUS: AtomicU8 = AtomicU8::new(0);

#[embassy_executor::task]
async fn i2c_task(
    p: I2CResources,
    sender: Sender<'static, RawMutexUsed, Command, CHANNEL_BUFFER_SIZE>,
) {
    let mut config = i2c_slave::Config::default();
    config.addr = DEV_ADDR;
    let mut dev = i2c_slave::I2cSlave::new(p.i2c1, p.scl, p.sda, Irqs, config);

    loop {
        let mut buf = [0u8; 128];

        match dev.listen(&mut buf).await {
            Ok(i2c_slave::Command::GeneralCall(len)) => {
                info!("Device received general call write: {:x}", &buf[..len])
            }
            Ok(i2c_slave::Command::Read) => {
                info!("Device received a read command");
                loop {
                    match dev
                        .respond_to_read(&[ERROR_VALUE.load(Ordering::Relaxed)])
                        .await
                    {
                        Ok(status) => match status {
                            i2c_slave::ReadStatus::Done => break,
                            i2c_slave::ReadStatus::NeedMoreBytes => (),
                            i2c_slave::ReadStatus::LeftoverBytes(n) => {
                                info!("tried to write {} extra bytes", n);
                                break;
                            }
                        },
                        Err(e) => error!("error while responding {:?}", e),
                    }
                }
            }
            Ok(i2c_slave::Command::Write(len)) => {
                info!("Device received write: {:x}", &buf[..len]);

                if len > 0 {
                    match I2CCommand::try_read_from_prefix(&buf[..len]) {
                        Ok((I2CCommand::SetSpeed, args)) => {
                            info!("Set speed command detected");
                            match SetSpeedArgs::try_read_from_bytes(args) {
                                Ok(speed_arg) => {
                                    info!("Setting the speed to {} RMP", speed_arg.speed);
                                    ERROR_VALUE.and(!ERROR_INVALID_COMMAND, Ordering::Relaxed);
                                    sender.send(Command::SetSpeed(speed_arg.speed)).await;
                                }
                                Err(e) => {
                                    info!(
                                        "Error parsing the set speed command args: {}",
                                        Debug2Format(&e)
                                    );
                                    ERROR_VALUE.or(ERROR_INVALID_COMMAND, Ordering::Relaxed);
                                }
                            }
                        }
                        Ok((I2CCommand::Run, args)) => {
                            info!("Run to degree command detected");
                            match RunToDegArgs::try_read_from_bytes(args) {
                                Ok(data) => {
                                    info!(
                                        "Running the stepper to {} deg with timeout = {}ms",
                                        data.deg, data.timeout
                                    );
                                    ERROR_VALUE.and(!ERROR_INVALID_COMMAND, Ordering::Relaxed);
                                    sender.send(Command::RunToDeg(data)).await
                                }
                                Err(e) => {
                                    info!(
                                        "Error parsing the run to degree command args: {}",
                                        Debug2Format(&e)
                                    );

                                    ERROR_VALUE.or(ERROR_INVALID_COMMAND, Ordering::Relaxed);
                                }
                            };
                        }
                        Ok((I2CCommand::RunToStep, args)) => {
                            match RunToStepArgs::try_read_from_bytes(args) {
                                Ok(data) => {
                                    info!(
                                        "Running the stepper to {} steps with timeout = {}ms",
                                        data.step, data.timeout
                                    );
                                    ERROR_VALUE.and(!ERROR_INVALID_COMMAND, Ordering::Relaxed);
                                    sender.send(Command::RunToStep(data)).await
                                }
                                Err(e) => {
                                    info!(
                                        "Error parsing the run to step command args: {}",
                                        Debug2Format(&e)
                                    );

                                    ERROR_VALUE.or(ERROR_INVALID_COMMAND, Ordering::Relaxed);
                                }
                            };
                        }
                        Ok((I2CCommand::Stop, _args)) => {
                            info!("Received a stop command, stopping the stepper");
                            ERROR_VALUE.and(!ERROR_INVALID_COMMAND, Ordering::Relaxed);
                            sender.send(Command::Stop).await
                        }
                        Err(_) => {
                            info!("Unknown command received: {:x}", buf[0]);
                            ERROR_VALUE.or(ERROR_INVALID_COMMAND, Ordering::Relaxed);
                        }
                    }
                }
            }
            Ok(i2c_slave::Command::WriteRead(_)) => {
                // info!("device received write read: {:x}", &buf[..len]);

                match dev
                    .respond_and_fill(
                        &[
                            STEPPER_STATUS.load(Ordering::Relaxed),
                            ERROR_VALUE.load(Ordering::Relaxed),
                        ],
                        0x00,
                    )
                    .await
                {
                    Ok(_) =>
                    /* info!("response read status {:?}", read_status) */
                    {
                        ()
                    }
                    Err(e) => error!("error while responding {:?}", e),
                }
            }
            Err(e) => error!("Listen error: {:?}", e),
        }
    }
}

static STOP_STEPPER_SIGNAL: signal::Signal<RawMutexUsed, ()> = signal::Signal::new();
static NEXT_STEPPER_SPEED: AtomicU16 = AtomicU16::new(0);

enum RunTarget {
    Deg(f32),
    Step(u16),
}

#[embassy_executor::task]
async fn run_stepper_task(
    stepper_mutex: &'static Mutex<RawMutexUsed, Stepper<'static>>,
    target: RunTarget,
    timeout: u64,
) {
    info!("Starting a stepper run");
    let mut stepper = stepper_mutex.lock().await;
    info!("Acquired stepper lock");

    match target {
        RunTarget::Deg(deg) => {
            info!("Set the target to {} deg", deg);
            stepper.set_target_deg(deg);
        }
        RunTarget::Step(step) => {
            info!("Set the target to {} steps", step);
            stepper.set_target(step);
        }
    }

    let new_speed = NEXT_STEPPER_SPEED.load(Ordering::Relaxed);

    if new_speed > 0 {
        info!(
            "Received a new stepper speed in the meantime - {} RPM",
            new_speed
        );
        stepper.set_speed(new_speed);
    }

    info!("Running the stepper");
    STEPPER_STATUS.or(STEPPER_STATUS_BIT, Ordering::Relaxed);
    ERROR_VALUE.and(!ERROR_SERVO_STUCK, Ordering::Relaxed);

    match select3(
        stepper.run(),
        STOP_STEPPER_SIGNAL.wait(),
        Timer::after_millis(timeout),
    )
    .await
    {
        Either3::First(_) => {
            info!("Stepper finished running");
        }
        Either3::Second(_) => {
            info!("Stepper was stopped early");
            stepper.stop().await;
        }
        Either3::Third(_) => {
            info!("The timeout has passed first");
            stepper.stop().await;
            ERROR_VALUE.or(ERROR_SERVO_STUCK, Ordering::Relaxed);
        }
    };

    STEPPER_STATUS.and(!STEPPER_STATUS_BIT, Ordering::Relaxed);
}

static ADC_VALUE: AtomicU16 = AtomicU16::new(0);

#[embassy_executor::task]
async fn adc_monitor() {
    loop {
        let val = ADC_VALUE.load(Ordering::Relaxed);

        info!(
            "ADC value = {}, ({} deg)",
            val,
            interpolate(
                val as f32,
                (ADC_MIN_VALUE as f32, ADC_MAX_VALUE as f32),
                (MIN_DEG_VALUE, MAX_DEG_VALUE)
            )
        );
        Timer::after_millis(100).await;
    }
}

#[embassy_executor::task]
async fn adc_writer(p: AdcResources) {
    let mut adc = adc::Adc::new(p.adc, Irqs, adc::Config::default());
    let mut pin = adc::Channel::new_pin(p.adc_pin, Pull::None);

    loop {
        let val = adc.read(&mut pin).await.unwrap();

        ADC_VALUE.store(val, Ordering::Relaxed);

        Timer::after_millis(1).await;
    }
}

#[embassy_executor::task]
async fn stepper_controller(
    spawner: Spawner,
    receiver: Receiver<'static, RawMutexUsed, Command, CHANNEL_BUFFER_SIZE>,
    p: StepperResources,
) {
    info!("Starting the stepper controller");

    STEPPER_STATUS.store(0, Ordering::Relaxed);

    static STEPPER: StaticCell<Mutex<RawMutexUsed, Stepper<'static>>> = StaticCell::new();
    let stepper_mutex = STEPPER.init(Mutex::new(Stepper::new_four_wire(
        2048,
        Output::new(p.pin1, Level::Low),
        Output::new(p.pin2, Level::Low),
        Output::new(p.pin3, Level::Low),
        Output::new(p.pin4, Level::Low),
        StepMode::FullStep,
        &ADC_VALUE,
    )));

    loop {
        match receiver.receive().await {
            Command::Stop => {
                info!("Received a stop command, signaling the stop");
                STOP_STEPPER_SIGNAL.signal(());
                Timer::after_millis(1).await;
                STOP_STEPPER_SIGNAL.reset();
            }
            Command::RunToDeg(RunToDegArgs { deg, timeout }) => {
                info!(
                    "Received a run to deg command (deg = {}), signaling the stop and starting a new run",
                    deg
                );
                STOP_STEPPER_SIGNAL.signal(());
                Timer::after_millis(1).await;
                STOP_STEPPER_SIGNAL.reset();
                spawner
                    .spawn(run_stepper_task(
                        stepper_mutex,
                        RunTarget::Deg(deg),
                        timeout,
                    ))
                    .unwrap()
            }
            Command::RunToStep(RunToStepArgs { step, timeout }) => {
                info!(
                    "Received a run to step command (step = {}), signaling the stop and starting a new run",
                    step
                );
                STOP_STEPPER_SIGNAL.signal(());
                Timer::after_millis(1).await;
                STOP_STEPPER_SIGNAL.reset();
                spawner
                    .spawn(run_stepper_task(
                        stepper_mutex,
                        RunTarget::Step(step),
                        timeout,
                    ))
                    .unwrap()
            }
            Command::SetSpeed(speed) => {
                info!("Received a new speed, storing in the shared value");
                NEXT_STEPPER_SPEED.store(speed, Ordering::Relaxed);
            }
        }
    }
}

static mut CORE1_STACK: Stack<4096> = Stack::new();
static EXECUTOR0: StaticCell<Executor> = StaticCell::new();
static EXECUTOR1: StaticCell<Executor> = StaticCell::new();

#[cortex_m_rt::entry]
unsafe fn main() -> ! {
    info!("Program start");
    let p = embassy_rp::init(Default::default());

    let r = split_resources!(p);

    static CHANNEL: Channel<RawMutexUsed, Command, CHANNEL_BUFFER_SIZE> = Channel::new();

    spawn_core1(
        p.CORE1,
        unsafe { &mut *core::ptr::addr_of_mut!(CORE1_STACK) },
        move || {
            let executor1 = EXECUTOR1.init(Executor::new());
            executor1.run(|spawner| {
                spawner.spawn(adc_monitor()).unwrap();
                spawner.spawn(adc_writer(r.adc_writer)).unwrap();
                spawner
                    .spawn(stepper_controller(spawner, CHANNEL.receiver(), r.stepper))
                    .unwrap()
            });
        },
    );

    let executor0 = EXECUTOR0.init(Executor::new());
    executor0.run(|spawner| {
        spawner.spawn(i2c_task(r.i2c, CHANNEL.sender())).unwrap();
    });
}

"""Calibrate platter spinning threshold and tonearm delay on Raspberry Pi hardware."""

import argparse
from dataclasses import dataclass
import time


GPIO_PIN = 24
SAMPLE_INTERVAL_SECONDS = 1

MIN_SPINNING_RPM = 1000
SPIN_UP_OBSERVATION_WINDOW_SECONDS = 3
SPIN_UP_RPM_INCREASE = 500
STOPPED_RPM_THRESHOLD = 1000
STOPPED_SAMPLE_COUNT = 4
STOPPED_TOTAL_RPM_DROP = 1000


@dataclass(frozen=True)
class RpmSample:
    sample_time: float
    rpm: float


class PulseCounter:
    def __init__(self):
        self.count = 0

    def pulse(self):
        self.count += 1

    def reset(self):
        self.count = 0


def calculate_rpm(pulse_count, elapsed_seconds):
    if elapsed_seconds <= 0:
        return 0.0
    return (pulse_count / elapsed_seconds) * 60


def is_spinning(samples):
    if not samples:
        return False

    latest = samples[-1]
    if latest.rpm <= MIN_SPINNING_RPM:
        return False

    lookback_time = latest.sample_time - SPIN_UP_OBSERVATION_WINDOW_SECONDS
    comparison_sample = None
    comparison_index = None
    for index, sample in enumerate(samples):
        if sample.sample_time <= lookback_time:
            comparison_sample = sample
            comparison_index = index
        else:
            break

    if comparison_sample is None:
        return False

    rpm_change = latest.rpm - comparison_sample.rpm
    observation_window = samples[comparison_index:]
    strictly_decreasing = all(
        previous.rpm > current.rpm
        for previous, current in zip(observation_window, observation_window[1:])
    )
    actively_spinning_up = rpm_change > SPIN_UP_RPM_INCREASE
    already_spinning_steadily = (
        comparison_sample.rpm > MIN_SPINNING_RPM
        and abs(rpm_change) <= SPIN_UP_RPM_INCREASE
        and not strictly_decreasing
    )
    return actively_spinning_up or already_spinning_steadily


def is_stopped(samples):
    if not samples:
        return False

    latest = samples[-1]
    if latest.rpm < STOPPED_RPM_THRESHOLD:
        return True

    decreasing_run_start = len(samples) - 1
    while (
        decreasing_run_start > 0
        and samples[decreasing_run_start - 1].rpm > samples[decreasing_run_start].rpm
    ):
        decreasing_run_start -= 1

    decreasing_run = samples[decreasing_run_start:]
    if len(decreasing_run) < STOPPED_SAMPLE_COUNT:
        return False

    total_drop = decreasing_run[0].rpm - decreasing_run[-1].rpm
    return total_drop >= STOPPED_TOTAL_RPM_DROP


def prune_samples(samples):
    latest = samples[-1]
    earliest_time = latest.sample_time - SPIN_UP_OBSERVATION_WINDOW_SECONDS
    while (
        len(samples) > STOPPED_SAMPLE_COUNT
        and len(samples) > 1
        and samples[1].sample_time <= earliest_time
    ):
        samples.pop(0)


def create_sensor(counter):
    from gpiozero import DigitalInputDevice

    sensor = DigitalInputDevice(GPIO_PIN, pull_up=True)
    sensor.when_activated = counter.pulse
    return sensor


def sample_rpm(counter, start_time):
    now = time.monotonic()
    elapsed = now - start_time
    return now, calculate_rpm(counter.count, elapsed)


def wait_for_spinning_threshold(counter):
    print(
        "Sampling platter sensor. Waiting for spin-up above "
        f"{MIN_SPINNING_RPM:.2f} RPM with more than "
        f"{SPIN_UP_RPM_INCREASE:.2f} RPM increase over "
        f"{SPIN_UP_OBSERVATION_WINDOW_SECONDS:.2f} seconds..."
    )

    start_time = time.monotonic()
    samples = []
    while True:
        time.sleep(SAMPLE_INTERVAL_SECONDS)

        now, rpm = sample_rpm(counter, start_time)
        samples.append(RpmSample(now, rpm))
        prune_samples(samples)

        stopped = is_stopped(samples)
        if is_spinning(samples):
            print(
                f"Spin-up detected: {rpm:.2f} RPM. "
                "Tonearm delay timing started."
            )
            return time.monotonic()

        print(
            f"Measured spinning value: {rpm:.2f} RPM "
            f"(spinning={is_spinning(samples)}, stopped={stopped})"
        )

        counter.reset()
        start_time = now


def wait_for_stopped(counter):
    print(
        "Sampling platter sensor. Waiting for stopped state below "
        f"{STOPPED_RPM_THRESHOLD:.2f} RPM or "
        f"{STOPPED_SAMPLE_COUNT} decreasing samples with at least "
        f"{STOPPED_TOTAL_RPM_DROP:.2f} RPM total drop..."
    )

    start_time = time.monotonic()
    samples = []
    while True:
        time.sleep(SAMPLE_INTERVAL_SECONDS)

        now, rpm = sample_rpm(counter, start_time)
        samples.append(RpmSample(now, rpm))
        prune_samples(samples)

        stopped = is_stopped(samples)
        print(f"Measured spinning value: {rpm:.2f} RPM (stopped={stopped})")

        if stopped:
            print(f"Stopped detected: {rpm:.2f} RPM.")
            return time.monotonic()

        counter.reset()
        start_time = now


def run_calibration():
    counter = PulseCounter()
    sensor = create_sensor(counter)

    try:
        timer_started_at = wait_for_spinning_threshold(counter)
        input("Press Enter when the needle reaches the platter...")
        elapsed_ms = (time.monotonic() - timer_started_at) * 1000
        print(f"Tonearm delay: {elapsed_ms:.0f} ms")
    finally:
        sensor.close()


def run_stopped_detection():
    counter = PulseCounter()
    sensor = create_sensor(counter)

    try:
        wait_for_stopped(counter)
    finally:
        sensor.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Calibrate platter spin-up timing or test stopped detection."
    )
    parser.add_argument(
        "--mode",
        choices=("delay", "stop"),
        default="delay",
        help=(
            "Run tonearm delay calibration, or sample until stopped detection "
            "triggers."
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.mode == "stop":
        run_stopped_detection()
    else:
        run_calibration()

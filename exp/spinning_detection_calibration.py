"""Calibrate platter spinning threshold and tonearm delay on Raspberry Pi hardware."""

import time


GPIO_PIN = 24
SAMPLE_INTERVAL_SECONDS = 5

# Edit this before running on the turntable hardware.
SPINNING_RPM_THRESHOLD = 5500


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


def create_sensor(counter):
    from gpiozero import DigitalInputDevice

    sensor = DigitalInputDevice(GPIO_PIN, pull_up=True)
    sensor.when_activated = counter.pulse
    return sensor


def wait_for_spinning_threshold(counter):
    print(
        "Sampling platter sensor. Waiting for "
        f"{SPINNING_RPM_THRESHOLD:.2f} RPM or higher..."
    )

    start_time = time.monotonic()
    while True:
        time.sleep(SAMPLE_INTERVAL_SECONDS)

        now = time.monotonic()
        elapsed = now - start_time
        rpm = calculate_rpm(counter.count, elapsed)

        if rpm >= SPINNING_RPM_THRESHOLD:
            print(
                f"Threshold reached: {rpm:.2f} RPM. "
                "Tonearm delay timing started."
            )
            return time.monotonic()

        print(
            f"Measured spinning value: {rpm:.2f} RPM "
            f"(threshold: {SPINNING_RPM_THRESHOLD:.2f} RPM)"
        )

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


if __name__ == "__main__":
    run_calibration()

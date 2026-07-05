import logging
import threading
import time
from dataclasses import dataclass


GPIO_PIN = 24
TONEARM_DELAY_AUTO = 12065
SAMPLE_INTERVAL_SECONDS = 1

MIN_SPINNING_RPM = 1000
SPIN_UP_OBSERVATION_WINDOW_SECONDS = 3
SPIN_UP_RPM_INCREASE = 500
STOPPED_RPM_THRESHOLD = 1000
STOPPED_SAMPLE_COUNT = 4
STOPPED_TOTAL_RPM_DROP = 1000

STATUS_PLAY = "play"
STATUS_STOP = "stop"


@dataclass(frozen=True)
class RpmSample:
    sample_time: float
    rpm: float


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

    decreasing_run_start = _decreasing_run_start(samples)
    decreasing_run = samples[decreasing_run_start:]
    if len(decreasing_run) < STOPPED_SAMPLE_COUNT:
        return False

    total_drop = decreasing_run[0].rpm - decreasing_run[-1].rpm
    return total_drop >= STOPPED_TOTAL_RPM_DROP


def _decreasing_run_start(samples):
    decreasing_run_start = len(samples) - 1
    while (
        decreasing_run_start > 0
        and samples[decreasing_run_start - 1].rpm > samples[decreasing_run_start].rpm
    ):
        decreasing_run_start -= 1
    return decreasing_run_start


def prune_samples(samples):
    if not samples:
        return

    latest = samples[-1]
    earliest_time = latest.sample_time - SPIN_UP_OBSERVATION_WINDOW_SECONDS
    time_keep_index = 0
    for index, sample in enumerate(samples):
        if sample.sample_time <= earliest_time:
            time_keep_index = index
        else:
            break

    keep_from = min(time_keep_index, _decreasing_run_start(samples))
    if keep_from > 0:
        del samples[:keep_from]


class PlaybackStatusDetector:
    STOPPED = "stopped"
    TONEARM_DELAY_PENDING = "tonearm_delay_pending"
    PLAYING = "playing"

    def __init__(
        self,
        tonearm_delay_ms=TONEARM_DELAY_AUTO,
        monotonic=time.monotonic,
    ):
        self.tonearm_delay_seconds = tonearm_delay_ms / 1000
        self.monotonic = monotonic
        self.state = self.STOPPED
        self.tonearm_delay_started_at = None
        self.playback_started_at = None
        self.last_emitted_playback_seconds = None
        self.samples = []
        self.last_spinning = False

    def sample(self, rpm, now=None):
        if now is None:
            now = self.monotonic()

        self.samples.append(RpmSample(now, rpm))
        prune_samples(self.samples)
        self.last_spinning = is_spinning(self.samples)
        stopped = is_stopped(self.samples)

        if stopped:
            if self.state == self.PLAYING:
                self._reset_playback()
                self.samples = []
                return status_message(STATUS_STOP)
            if self.state == self.TONEARM_DELAY_PENDING:
                self._reset_playback()
                self.samples = []
            return None

        if self.state == self.STOPPED:
            if self.last_spinning:
                self.state = self.TONEARM_DELAY_PENDING
                self.tonearm_delay_started_at = now
            return None

        if self.state == self.TONEARM_DELAY_PENDING:
            if now - self.tonearm_delay_started_at >= self.tonearm_delay_seconds:
                self.state = self.PLAYING
                self.playback_started_at = now
                self.last_emitted_playback_seconds = 0
                return status_message(STATUS_PLAY, time_value=format_playback_time(0))
            return None

        if self.state == self.PLAYING:
            playback_seconds = int(now - self.playback_started_at)
            if playback_seconds > self.last_emitted_playback_seconds:
                self.last_emitted_playback_seconds = playback_seconds
                return status_message(STATUS_PLAY, time_value=format_playback_time(playback_seconds))

        return None

    def classify_spinning_with(self, rpm, now=None):
        if now is None:
            now = self.monotonic()
        samples = [*self.samples, RpmSample(now, rpm)]
        prune_samples(samples)
        return is_spinning(samples)

    def _reset_playback(self):
        self.state = self.STOPPED
        self.tonearm_delay_started_at = None
        self.playback_started_at = None
        self.last_emitted_playback_seconds = None


class PulseCounter:
    def __init__(self):
        self.count = 0
        self.lock = threading.Lock()

    def pulse(self):
        with self.lock:
            self.count += 1

    def reset(self):
        with self.lock:
            count = self.count
            self.count = 0
        return count


def calculate_rpm(pulse_count, elapsed_seconds):
    if elapsed_seconds <= 0:
        return 0.0
    return (pulse_count / elapsed_seconds) * 60


class GpioRpmReader:
    def __init__(self, pin=GPIO_PIN, monotonic=time.monotonic):
        from gpiozero import DigitalInputDevice

        self.counter = PulseCounter()
        self.monotonic = monotonic
        self.last_sample_at = monotonic()
        self.sensor = DigitalInputDevice(pin, pull_up=True)
        self.sensor.when_activated = self.counter.pulse

    def read_rpm(self):
        now = self.monotonic()
        elapsed = now - self.last_sample_at
        pulse_count = self.counter.reset()
        self.last_sample_at = now
        return calculate_rpm(pulse_count, elapsed)

    def close(self):
        self.sensor.close()


def create_gpio_rpm_reader():
    return GpioRpmReader()


def format_playback_time(total_seconds):
    minutes, seconds = divmod(max(int(total_seconds), 0), 60)
    return f"{minutes:02d}:{seconds:02d}"


def status_message(status, time_value=None):
    data = {"status": status}
    if time_value is not None:
        data["time"] = time_value
    return {"event": "status", "data": data}


def publish_playback_status_once(detector, read_rpm, broadcast, logger=None):
    rpm = read_rpm()
    now = detector.monotonic()
    is_sample_spinning = detector.classify_spinning_with(rpm, now=now)
    if logger is not None:
        logger.info(
            "Playback sensor RPM sample: %.2f RPM (spinning=%s)",
            rpm,
            is_sample_spinning,
        )

    message = detector.sample(rpm, now=now)
    if message is None:
        return None

    data = message.get("data") or {}
    if logger is not None and (data.get("status") == STATUS_STOP or data.get("time") == "00:00"):
        detected_event = "start" if data.get("status") == STATUS_PLAY else "stop"
        logger.info("Playback status event sent: %s at %.2f RPM", detected_event, rpm)

    broadcast(message)
    return message


def run_playback_status_publisher(
    broadcast,
    create_reader=create_gpio_rpm_reader,
    interval_seconds=SAMPLE_INTERVAL_SECONDS,
    detector=None,
    sleep=time.sleep,
    logger=None,
):
    if logger is None:
        logger = logging.getLogger(__name__)

    reader = None
    try:
        reader = create_reader()
    except Exception as e:
        logger.error("Failed to initialize RPM reader: %s", e)
        return

    if detector is None:
        detector = PlaybackStatusDetector()

    try:
        while True:
            try:
                publish_playback_status_once(detector, reader.read_rpm, broadcast, logger=logger)
            except Exception as e:
                logger.error("Failed to publish playback status: %s", e)
            sleep(interval_seconds)
    finally:
        close = getattr(reader, "close", None)
        if close is not None:
            close()

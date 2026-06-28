import logging
import threading
import time


GPIO_PIN = 24
SPINNING_RPM_THRESHOLD = 4500
TONEARM_DELAY_AUTO = 10713
SAMPLE_INTERVAL_SECONDS = 1

STATUS_PLAY = "play"
STATUS_STOP = "stop"


class PlaybackStatusDetector:
    STOPPED = "stopped"
    THRESHOLD_REACHED = "threshold_reached"
    PLAYING = "playing"

    def __init__(
        self,
        rpm_threshold=SPINNING_RPM_THRESHOLD,
        tonearm_delay_ms=TONEARM_DELAY_AUTO,
        monotonic=time.monotonic,
    ):
        self.rpm_threshold = rpm_threshold
        self.tonearm_delay_seconds = tonearm_delay_ms / 1000
        self.monotonic = monotonic
        self.state = self.STOPPED
        self.threshold_reached_at = None
        self.playback_started_at = None
        self.last_emitted_playback_seconds = None

    def sample(self, rpm, now=None):
        if now is None:
            now = self.monotonic()

        if rpm < self.rpm_threshold:
            was_playing = self.state == self.PLAYING
            self.state = self.STOPPED
            self.threshold_reached_at = None
            self.playback_started_at = None
            self.last_emitted_playback_seconds = None
            return status_message(STATUS_STOP) if was_playing else None

        if self.state == self.STOPPED:
            self.state = self.THRESHOLD_REACHED
            self.threshold_reached_at = now
            return None

        if self.state == self.THRESHOLD_REACHED:
            if now - self.threshold_reached_at >= self.tonearm_delay_seconds:
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


def publish_playback_status_once(detector, read_rpm, broadcast):
    rpm = read_rpm()
    message = detector.sample(rpm)
    if message is None:
        return None

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
                publish_playback_status_once(detector, reader.read_rpm, broadcast)
            except Exception as e:
                logger.error("Failed to publish playback status: %s", e)
            sleep(interval_seconds)
    finally:
        close = getattr(reader, "close", None)
        if close is not None:
            close()

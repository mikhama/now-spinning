import unittest
from unittest.mock import Mock

from api.playback_status import (
    SAMPLE_INTERVAL_SECONDS,
    SPINNING_RPM_THRESHOLD,
    TONEARM_DELAY_AUTO,
    PlaybackStatusDetector,
    calculate_rpm,
    format_playback_time,
    publish_playback_status_once,
    run_playback_status_publisher,
)


class FakeReader:
    def __init__(self, rpms):
        self.rpms = list(rpms)
        self.closed = False

    def read_rpm(self):
        if not self.rpms:
            raise KeyboardInterrupt()
        return self.rpms.pop(0)

    def close(self):
        self.closed = True


class PlaybackStatusDetectorTestCase(unittest.TestCase):
    def status_message(self, status, time_value=None):
        data = {"status": status}
        if time_value is not None:
            data["time"] = time_value
        return {"event": "status", "data": data}

    def test_below_threshold_samples_produce_no_events(self):
        detector = PlaybackStatusDetector()

        self.assertIsNone(detector.sample(SPINNING_RPM_THRESHOLD - 1, now=0))
        self.assertIsNone(detector.sample(0, now=1))
        self.assertEqual(detector.state, PlaybackStatusDetector.STOPPED)

    def test_threshold_crossing_waits_for_tonearm_delay_then_emits_play(self):
        detector = PlaybackStatusDetector()

        self.assertIsNone(detector.sample(SPINNING_RPM_THRESHOLD, now=0))
        self.assertIsNone(detector.sample(SPINNING_RPM_THRESHOLD, now=10.712))
        self.assertEqual(
            detector.sample(SPINNING_RPM_THRESHOLD, now=10.713),
            self.status_message("play", "00:00"),
        )
        self.assertEqual(detector.state, PlaybackStatusDetector.PLAYING)

    def test_drop_before_tonearm_delay_resets_pending_playback_without_events(self):
        detector = PlaybackStatusDetector()

        self.assertIsNone(detector.sample(SPINNING_RPM_THRESHOLD, now=0))
        self.assertIsNone(detector.sample(SPINNING_RPM_THRESHOLD - 1, now=5))
        self.assertEqual(detector.state, PlaybackStatusDetector.STOPPED)
        self.assertIsNone(detector.sample(SPINNING_RPM_THRESHOLD, now=8))
        self.assertIsNone(detector.sample(SPINNING_RPM_THRESHOLD, now=18))
        self.assertEqual(
            detector.sample(SPINNING_RPM_THRESHOLD, now=18.713),
            self.status_message("play", "00:00"),
        )

    def test_drop_after_playback_started_emits_stop_once(self):
        detector = PlaybackStatusDetector()

        detector.sample(SPINNING_RPM_THRESHOLD, now=0)
        self.assertEqual(
            detector.sample(SPINNING_RPM_THRESHOLD, now=10.713),
            self.status_message("play", "00:00"),
        )
        self.assertEqual(
            detector.sample(SPINNING_RPM_THRESHOLD - 1, now=10),
            self.status_message("stop"),
        )
        self.assertEqual(detector.state, PlaybackStatusDetector.STOPPED)

    def test_repeated_playing_samples_emit_updated_time_without_duplicate_seconds(self):
        detector = PlaybackStatusDetector()

        detector.sample(SPINNING_RPM_THRESHOLD, now=0)
        self.assertEqual(
            detector.sample(SPINNING_RPM_THRESHOLD, now=10.713),
            self.status_message("play", "00:00"),
        )
        self.assertIsNone(detector.sample(SPINNING_RPM_THRESHOLD + 100, now=11.2))
        self.assertEqual(
            detector.sample(SPINNING_RPM_THRESHOLD + 100, now=11.8),
            self.status_message("play", "00:01"),
        )
        self.assertEqual(
            detector.sample(SPINNING_RPM_THRESHOLD + 100, now=72),
            self.status_message("play", "01:01"),
        )

    def test_duplicate_stop_events_are_suppressed(self):
        detector = PlaybackStatusDetector()

        detector.sample(SPINNING_RPM_THRESHOLD, now=0)
        detector.sample(SPINNING_RPM_THRESHOLD, now=10.713)
        self.assertEqual(
            detector.sample(SPINNING_RPM_THRESHOLD - 1, now=12),
            self.status_message("stop"),
        )
        self.assertIsNone(detector.sample(0, now=13))

    def test_publish_playback_status_once_broadcasts_existing_status_format_with_time(self):
        detector = PlaybackStatusDetector()
        detector.sample(SPINNING_RPM_THRESHOLD, now=0)
        detector.monotonic = lambda: TONEARM_DELAY_AUTO / 1000
        sent_messages = []

        message = publish_playback_status_once(
            detector,
            read_rpm=lambda: SPINNING_RPM_THRESHOLD,
            broadcast=sent_messages.append,
        )

        expected = {"event": "status", "data": {"status": "play", "time": "00:00"}}
        self.assertEqual(message, expected)
        self.assertEqual(sent_messages, [expected])

    def test_format_playback_time_returns_zero_padded_minutes_and_seconds(self):
        self.assertEqual(format_playback_time(0), "00:00")
        self.assertEqual(format_playback_time(1), "00:01")
        self.assertEqual(format_playback_time(210), "03:30")
        self.assertEqual(format_playback_time(-1), "00:00")

    def test_calculate_rpm_uses_pulse_count_over_elapsed_seconds(self):
        self.assertEqual(calculate_rpm(100, 1), 6000)
        self.assertEqual(calculate_rpm(100, 0), 0.0)

    def test_publisher_samples_every_second_and_handles_reader_setup_failure(self):
        errors = []

        run_playback_status_publisher(
            broadcast=Mock(),
            create_reader=Mock(side_effect=RuntimeError("no gpio")),
            sleep=Mock(),
            logger=Mock(error=lambda message, error: errors.append((message, error))),
        )

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0][0], "Failed to initialize RPM reader: %s")
        self.assertEqual(str(errors[0][1]), "no gpio")

    def test_publisher_uses_one_second_sample_interval(self):
        reader = FakeReader([SPINNING_RPM_THRESHOLD])
        sleeps = []

        with self.assertRaises(KeyboardInterrupt):
            run_playback_status_publisher(
                broadcast=Mock(),
                create_reader=lambda: reader,
                sleep=lambda seconds: sleeps.append(seconds),
            )

        self.assertEqual(sleeps, [SAMPLE_INTERVAL_SECONDS])
        self.assertTrue(reader.closed)


if __name__ == "__main__":
    unittest.main()

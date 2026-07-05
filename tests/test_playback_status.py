import unittest
from unittest.mock import Mock

from api.playback_status import (
    MIN_SPINNING_RPM,
    SAMPLE_INTERVAL_SECONDS,
    TONEARM_DELAY_AUTO,
    PlaybackStatusDetector,
    SPIN_UP_OBSERVATION_WINDOW_SECONDS,
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

    def spin_up_detector(self):
        detector = PlaybackStatusDetector()
        detector.sample(900, now=0)
        detector.sample(1601, now=SPIN_UP_OBSERVATION_WINDOW_SECONDS + 0.1)
        return detector

    def test_automatic_tonearm_delay_uses_measured_value(self):
        self.assertEqual(TONEARM_DELAY_AUTO, 12065)

    def test_rpm_below_or_equal_to_minimum_spinning_value_produces_no_play_event(self):
        detector = PlaybackStatusDetector()

        self.assertIsNone(detector.sample(MIN_SPINNING_RPM, now=0))
        self.assertIsNone(detector.sample(MIN_SPINNING_RPM - 1, now=4))
        self.assertEqual(detector.state, PlaybackStatusDetector.STOPPED)

    def test_insufficient_spin_up_increase_does_not_start_tonearm_delay(self):
        detector = PlaybackStatusDetector()

        self.assertIsNone(detector.sample(900, now=0))
        self.assertIsNone(detector.sample(1300, now=3.1))
        self.assertEqual(detector.state, PlaybackStatusDetector.STOPPED)

    def test_spin_up_trend_waits_for_tonearm_delay_then_emits_play(self):
        detector = PlaybackStatusDetector()

        self.assertIsNone(detector.sample(900, now=0))
        self.assertIsNone(detector.sample(1601, now=3.1))
        self.assertEqual(detector.state, PlaybackStatusDetector.TONEARM_DELAY_PENDING)
        self.assertIsNone(detector.sample(1700, now=15.164))
        self.assertEqual(
            detector.sample(1700, now=15.165),
            self.status_message("play", "00:00"),
        )
        self.assertEqual(detector.state, PlaybackStatusDetector.PLAYING)

    def test_already_spinning_steady_rpm_starts_tonearm_delay(self):
        detector = PlaybackStatusDetector()

        self.assertIsNone(detector.sample(3300, now=0))
        self.assertIsNone(detector.sample(3350, now=1))
        self.assertIsNone(detector.sample(3325, now=2))
        self.assertIsNone(detector.sample(3340, now=3.1))
        self.assertEqual(detector.state, PlaybackStatusDetector.TONEARM_DELAY_PENDING)
        self.assertEqual(
            detector.sample(3345, now=15.165),
            self.status_message("play", "00:00"),
        )

    def test_strictly_decreasing_steady_range_rpm_does_not_start_tonearm_delay(self):
        detector = PlaybackStatusDetector()

        self.assertIsNone(detector.sample(3400, now=0))
        self.assertIsNone(detector.sample(3300, now=1))
        self.assertIsNone(detector.sample(3200, now=2))
        self.assertIsNone(detector.sample(3100, now=3.1))
        self.assertEqual(detector.state, PlaybackStatusDetector.STOPPED)

    def test_stopped_before_tonearm_delay_resets_pending_playback_without_events(self):
        detector = PlaybackStatusDetector()

        self.assertIsNone(detector.sample(900, now=0))
        self.assertIsNone(detector.sample(1601, now=3.1))
        self.assertEqual(detector.state, PlaybackStatusDetector.TONEARM_DELAY_PENDING)
        self.assertIsNone(detector.sample(900, now=4))
        self.assertEqual(detector.state, PlaybackStatusDetector.STOPPED)

    def test_rpm_below_stopped_threshold_after_playback_started_emits_stop_once(self):
        detector = self.spin_up_detector()

        self.assertEqual(detector.sample(1700, now=15.165), self.status_message("play", "00:00"))
        self.assertEqual(detector.sample(999, now=16), self.status_message("stop"))
        self.assertEqual(detector.state, PlaybackStatusDetector.STOPPED)

    def test_strictly_decreasing_run_after_playback_started_emits_stop_once(self):
        detector = self.spin_up_detector()

        self.assertEqual(detector.sample(4200, now=15.165), self.status_message("play", "00:00"))
        self.assertIsNone(detector.sample(4000, now=16))
        self.assertEqual(detector.sample(3600, now=17), self.status_message("play", "00:01"))
        self.assertEqual(detector.sample(3200, now=18), self.status_message("stop"))

    def test_repeated_playing_samples_emit_updated_time_without_duplicate_seconds(self):
        detector = self.spin_up_detector()

        self.assertEqual(
            detector.sample(1700, now=15.165),
            self.status_message("play", "00:00"),
        )
        self.assertIsNone(detector.sample(1800, now=15.8))
        self.assertEqual(
            detector.sample(1800, now=16.2),
            self.status_message("play", "00:01"),
        )
        self.assertEqual(
            detector.sample(1800, now=76.2),
            self.status_message("play", "01:01"),
        )

    def test_duplicate_stop_events_are_suppressed(self):
        detector = self.spin_up_detector()

        detector.sample(1700, now=15.165)
        self.assertEqual(
            detector.sample(999, now=16),
            self.status_message("stop"),
        )
        self.assertIsNone(detector.sample(0, now=17))

    def test_publish_playback_status_once_broadcasts_existing_status_format_with_time(self):
        detector = self.spin_up_detector()
        detector.monotonic = lambda: 15.165
        sent_messages = []

        message = publish_playback_status_once(
            detector,
            read_rpm=lambda: 1700,
            broadcast=sent_messages.append,
        )

        expected = {"event": "status", "data": {"status": "play", "time": "00:00"}}
        self.assertEqual(message, expected)
        self.assertEqual(sent_messages, [expected])

    def test_publish_playback_status_logs_sensor_samples_and_start_stop_events(self):
        detector = self.spin_up_detector()
        logger = Mock()
        sent_messages = []

        detector.monotonic = lambda: 15.165
        publish_playback_status_once(
            detector,
            read_rpm=lambda: 1700.345,
            broadcast=sent_messages.append,
            logger=logger,
        )

        detector.monotonic = lambda: 16.165
        publish_playback_status_once(
            detector,
            read_rpm=lambda: 1720,
            broadcast=sent_messages.append,
            logger=logger,
        )

        detector.monotonic = lambda: 17.165
        publish_playback_status_once(
            detector,
            read_rpm=lambda: 998.75,
            broadcast=sent_messages.append,
            logger=logger,
        )

        self.assertEqual(logger.info.call_count, 5)
        logger.info.assert_any_call(
            "Playback sensor RPM sample: %.2f RPM (spinning=%s)",
            1700.345,
            True,
        )
        logger.info.assert_any_call(
            "Playback sensor RPM sample: %.2f RPM (spinning=%s)",
            1720,
            True,
        )
        logger.info.assert_any_call(
            "Playback sensor RPM sample: %.2f RPM (spinning=%s)",
            998.75,
            False,
        )
        logger.info.assert_any_call(
            "Playback status event sent: %s at %.2f RPM",
            "start",
            1700.345,
        )
        logger.info.assert_any_call(
            "Playback status event sent: %s at %.2f RPM",
            "stop",
            998.75,
        )

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
        reader = FakeReader([MIN_SPINNING_RPM])
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

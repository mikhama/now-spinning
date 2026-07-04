import unittest

from api.stylus_hours import StylusHoursTracker, parse_elapsed_seconds


class StylusHoursTrackerTestCase(unittest.TestCase):
    def setUp(self):
        self.active_stylus = {"id": "1", "hours": 100.0}
        self.increments = []
        self.tracker = StylusHoursTracker(
            get_active_stylus=lambda: self.active_stylus,
            increment_stylus_hours=self.increment,
        )

    def increment(self, stylus_id, delta_hours):
        self.increments.append((stylus_id, delta_hours))
        return stylus_id == "1"

    def status_message(self, status, time_value=None):
        data = {"status": status}
        if time_value is not None:
            data["time"] = time_value
        return {"event": "status", "data": data}

    def test_parse_elapsed_seconds_accepts_mm_ss(self):
        self.assertEqual(parse_elapsed_seconds("10:00"), 600)
        self.assertEqual(parse_elapsed_seconds("03:30"), 210)
        self.assertIsNone(parse_elapsed_seconds("bad"))
        self.assertIsNone(parse_elapsed_seconds("00:60"))

    def test_active_stylus_accrues_from_zero_to_ten_minutes(self):
        self.assertEqual(self.tracker.process_message(self.status_message("play", "00:00")), [])

        events = self.tracker.process_message(self.status_message("play", "10:00"))

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "stylus_hours")
        self.assertEqual(events[0]["data"]["stylus_id"], "1")
        self.assertAlmostEqual(events[0]["data"]["hours"], 100.1666667)

    def test_no_active_stylus_skips_accrual_and_does_not_back_count_later(self):
        self.active_stylus = None
        self.assertEqual(self.tracker.process_message(self.status_message("play", "00:00")), [])

        self.active_stylus = {"id": "1", "hours": 100.0}
        self.assertEqual(self.tracker.process_message(self.status_message("play", "10:00")), [])

        events = self.tracker.process_message(self.status_message("play", "10:01"))
        self.assertAlmostEqual(events[0]["data"]["hours"], 100.0002778)

    def test_playback_emits_live_stylus_hours_update(self):
        self.tracker.process_message(self.status_message("play", "00:00"))

        events = self.tracker.process_message(self.status_message("play", "00:01"))

        self.assertEqual(
            events,
            [{"event": "stylus_hours", "data": {"stylus_id": "1", "hours": 100.00027777777778}}],
        )

    def test_ten_minutes_of_pending_playback_triggers_flush(self):
        self.tracker.process_message(self.status_message("play", "00:00"))
        self.tracker.process_message(self.status_message("play", "10:00"))

        self.assertEqual(len(self.increments), 1)
        self.assertEqual(self.increments[0][0], "1")
        self.assertAlmostEqual(self.increments[0][1], 600 / 3600)
        self.assertEqual(self.tracker.pending_seconds, 0)

    def test_less_than_ten_minutes_remains_pending(self):
        self.tracker.process_message(self.status_message("play", "00:00"))
        self.tracker.process_message(self.status_message("play", "09:59"))

        self.assertEqual(self.increments, [])
        self.assertEqual(self.tracker.pending_seconds, 599)

    def test_stop_flushes_all_pending_usage(self):
        self.tracker.process_message(self.status_message("play", "00:00"))
        self.tracker.process_message(self.status_message("play", "04:00"))

        self.tracker.process_message(self.status_message("stop"))

        self.assertEqual(len(self.increments), 1)
        self.assertAlmostEqual(self.increments[0][1], 240 / 3600)
        self.assertEqual(self.tracker.pending_seconds, 0)

    def test_reset_clears_runtime_hours_and_pending_usage(self):
        self.tracker.process_message(self.status_message("play", "00:00"))
        self.tracker.process_message(self.status_message("play", "04:00"))

        self.tracker.reset_stylus("1")

        self.assertEqual(self.tracker.pending_seconds, 0)
        self.assertEqual(self.tracker.current_hours, 0)
        self.assertIsNone(self.tracker.last_elapsed_seconds)


if __name__ == "__main__":
    unittest.main()

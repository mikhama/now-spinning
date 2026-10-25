from contextlib import ExitStack
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import os
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

import api.main as api_main
from api.services.db import database


class SessionHistoryApiTestCase(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        directory = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.stack.enter_context(patch.object(database, "DB_PATH", os.path.join(directory, "history.db")))
        database.init_db()
        with sqlite3.connect(database.DB_PATH) as conn:
            conn.executemany("INSERT INTO record (id,title,artist) VALUES (?,?,?)", [("A", "First", "Artist"), ("B", "Second", "Artist")])
            conn.executemany("INSERT INTO stylus VALUES (?, ?, ?, 500, 1000, ?)", [("1", "First", 10, 1), ("2", "Second", 20, 0)])
        self.stylus = api_main.create_stylus_hours_tracker()
        self.history = api_main.create_session_history_tracker()
        self.wall = datetime(2026, 10, 25, 10, tzinfo=timezone.utc)
        self.history.now = lambda: self.wall
        self.coordinator = Mock(cleanup_succeeded=True, run_forever=lambda: None)
        for name, value in {
            "stylus_hours_tracker": self.stylus, "session_history_tracker": self.history,
            "shutdown_started": threading.Event(), "shutdown_cleanup_lock": threading.Lock(),
            "shutdown_result": False, "nfc_coordinator": self.coordinator,
            "nfc_coordinator_thread": None, "nfc_coordinator_lock": threading.RLock(),
        }.items():
            self.stack.enter_context(patch.object(api_main, name, value))
        old_state = deepcopy(api_main.runtime_state)
        self.addCleanup(lambda: (api_main.runtime_state.clear(), api_main.runtime_state.update(old_state)))
        api_main.runtime_state.update(current_record_id=None, last_scan_data=None, status="stop", status_time=None, stylus_hours={})
        self.stack.enter_context(patch.dict(os.environ, {"KIOSK_SHUTDOWN_ENABLED": "true", "BOARDLESS_MODE": "false"}))
        self.client = api_main.app.test_client()
        self.select("A")

    def select(self, record):
        api_main.broadcast_message({"event": "current_record", "data": {"record_id": record}})

    def play(self, seconds):
        self.wall = datetime(2026, 10, 25, 10, tzinfo=timezone.utc) + timedelta(seconds=seconds)
        api_main.broadcast_message({"event": "status", "data": {"status": "play", "time": f"{seconds // 60:02}:{seconds % 60:02}"}})

    def stop(self):
        api_main.broadcast_message({"event": "status", "data": {"status": "stop"}})

    def durations(self):
        return [(r["record_id"], r["session_duration_sec"]) for r in database.get_playback_sessions()]

    def test_periodic_checkpoint_then_short_stop_save_both_trackers(self):
        self.play(0)
        self.play(599)
        self.assertEqual(self.durations(), [])
        self.play(600)
        self.assertEqual(self.durations(), [("A", 600)])
        self.play(634)
        self.stop()
        self.assertEqual(self.durations(), [("A", 600), ("A", 34)])
        self.assertAlmostEqual(database.get_active_stylus_hours()["hours"], 10 + 634 / 3600)
        rows = database.get_playback_sessions()
        self.assertEqual(datetime.fromisoformat(rows[1]["session_started_at"]) - datetime.fromisoformat(rows[0]["session_started_at"]), timedelta(seconds=600))

    def test_history_checkpoints_without_any_stylus(self):
        with sqlite3.connect(database.DB_PATH) as conn:
            conn.execute("DELETE FROM stylus")
        self.play(0)
        self.play(599)
        self.assertEqual(self.durations(), [])
        self.play(600)
        self.assertEqual(self.durations(), [("A", 600)])
        self.play(605)
        self.stop()
        self.assertEqual(self.durations(), [("A", 600), ("A", 5)])
        self.assertEqual(database.get_all_styli(), [])

    def test_stylus_checkpoint_also_saves_history_shorter_than_600_seconds(self):
        self.play(0)
        self.play(300)
        self.select("B")
        self.assertEqual(self.durations(), [("A", 300)])
        self.play(300)
        self.play(600)
        self.assertEqual(self.durations(), [("A", 300), ("B", 300)])
        self.assertEqual(self.stylus.pending_seconds, 0)

    def test_unknown_playback_adds_no_rows_or_separator(self):
        self.play(0)
        self.play(10)
        for record in ("", "missing", None):
            self.select(record)
            self.play(20)
            self.play(30)
        self.select("A")
        self.play(30)
        self.play(35)
        self.stop()
        self.assertEqual(self.durations(), [("A", 10), ("A", 5)])

    def test_record_change_and_counter_reset_close_before_counting_more(self):
        self.play(0)
        self.play(12)
        self.select("B")
        self.play(12)
        self.play(20)
        self.play(0)
        self.play(3)
        self.select("A")
        self.play(0)
        self.play(4)
        self.stop()
        # Counter reset moves wall time backwards in this fixture; insertion IDs
        # still prove the segment boundaries independently of report sorting.
        with sqlite3.connect(database.DB_PATH) as conn:
            rows = conn.execute("SELECT record_id, session_duration_sec FROM sessions_log ORDER BY id").fetchall()
        self.assertEqual(rows, [("A", 12), ("B", 8), ("B", 3), ("A", 4)])

    def test_stylus_reset_preserves_history_pending_seconds_and_baseline(self):
        self.play(0)
        self.play(12)
        self.assertEqual(self.client.post("/styli/1/reset").status_code, 200)
        self.assertEqual(self.history.pending_seconds, 12)
        self.play(20)
        self.stop()
        self.assertEqual(self.durations(), [("A", 20)])
        self.assertEqual(database.get_active_stylus_hours()["hours"], 0)

    def test_history_exception_on_stop_does_not_skip_stylus_save_or_lose_history(self):
        self.play(0)
        self.play(12)
        with patch.object(self.history, "save_sessions", side_effect=sqlite3.OperationalError("history write failed")):
            self.stop()
        self.assertEqual(self.history.pending_seconds, 12)
        self.assertEqual(self.stylus.pending_seconds, 0)
        self.assertIsNone(self.history.last_elapsed_seconds)
        self.stop()
        self.stop()
        self.assertEqual(self.durations(), [("A", 12)])
        self.assertAlmostEqual(database.get_active_stylus_hours()["hours"], 10 + 12 / 3600)

    def test_periodic_history_failure_still_saves_stylus_and_retries_once(self):
        self.play(0)
        with patch.object(self.history, "save_sessions", return_value=False):
            self.play(600)
        self.assertEqual(self.history.pending_seconds, 600)
        self.assertEqual(self.stylus.pending_seconds, 0)
        self.play(601)
        self.stop()
        self.assertEqual(self.durations(), [("A", 601)])
        self.assertAlmostEqual(database.get_active_stylus_hours()["hours"], 10 + 601 / 3600)

    def test_periodic_stylus_exception_still_commits_history(self):
        self.play(0)
        with patch.object(self.stylus, "increment_stylus_hours", side_effect=sqlite3.OperationalError("stylus write failed")):
            self.play(600)
        self.assertEqual(self.durations(), [("A", 600)])
        self.assertEqual(self.stylus.pending_seconds, 600)
        self.stop()
        self.stop()
        self.assertEqual(self.durations(), [("A", 600)])
        self.assertAlmostEqual(database.get_active_stylus_hours()["hours"], 10 + 600 / 3600)

    def check_power_failure(self, tracker, method):
        self.play(0)
        self.play(12)
        with patch.object(tracker, method, return_value=False), patch.object(api_main.sys, "platform", "linux"), patch.object(api_main.subprocess, "run") as poweroff, patch.object(api_main.threading, "Timer") as timer:
            for endpoint in ("/kiosk/exit", "/shutdown"):
                self.assertEqual(self.client.post(endpoint).status_code, 500)
            poweroff.assert_not_called()
            timer.assert_not_called()
        self.assertEqual(self.client.post("/kiosk/exit").status_code, 200)
        api_main.flush_pending_stylus_usage()
        self.assertEqual(self.durations(), [("A", 12)])
        self.assertAlmostEqual(database.get_active_stylus_hours()["hours"], 10 + 12 / 3600)

    def test_history_failure_cancels_both_power_actions(self):
        with patch.object(api_main.threading, "Timer"):
            self.check_power_failure(self.history, "save_sessions")

    def test_stylus_failure_cancels_both_power_actions_after_history_commits(self):
        with patch.object(api_main.threading, "Timer"):
            self.check_power_failure(self.stylus, "increment_stylus_hours")

    def test_both_save_exceptions_are_attempted_and_retained(self):
        self.play(0)
        self.play(12)
        with patch.object(self.history, "save_sessions", side_effect=OSError("history failed")) as history_save, patch.object(self.stylus, "increment_stylus_hours", side_effect=OSError("stylus failed")) as stylus_save:
            with self.assertRaises(RuntimeError):
                api_main.flush_pending_stylus_usage()
            history_save.assert_called_once()
            stylus_save.assert_called_once()
        self.assertEqual((self.history.pending_seconds, self.stylus.pending_seconds), (12, 12))
        api_main.flush_pending_stylus_usage()
        self.assertEqual(self.durations(), [("A", 12)])

    def test_stopped_selection_retries_history_and_saves_previous_stylus_before_switch(self):
        self.play(0)
        self.play(12)
        with patch.object(self.history, "save_sessions", return_value=False):
            self.stop()
            self.assertEqual(self.client.post("/styli/2/activate").status_code, 500)
        self.assertEqual(database.get_active_stylus_hours()["id"], "1")
        self.assertEqual(self.stylus.pending_seconds, 0)
        self.assertEqual(self.client.post("/styli/2/activate").status_code, 200)
        self.assertEqual(self.durations(), [("A", 12)])
        self.assertEqual(database.get_active_stylus_hours()["id"], "2")

    def test_repeated_cleanup_retries_pending_history_once_and_freezes_counting(self):
        self.play(0)
        self.play(12)
        with patch.object(self.history, "save_sessions", return_value=False):
            self.assertFalse(api_main.shutdown_application())
        self.assertEqual(self.stylus.pending_seconds, 0)
        self.assertEqual(self.history.pending_seconds, 12)
        self.play(20)
        self.assertEqual(self.history.pending_seconds, 12)
        self.assertTrue(api_main.shutdown_application())
        self.assertTrue(api_main.shutdown_application())
        self.coordinator.stop.assert_called_once()
        self.assertEqual(self.durations(), [("A", 12)])
        self.assertAlmostEqual(database.get_active_stylus_hours()["hours"], 10 + 12 / 3600)


if __name__ == "__main__":
    unittest.main()

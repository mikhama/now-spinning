import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import api.main as api_main
from api.services.db import database


class StylusSelectionTestCase(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        db_patch = patch.object(database, "DB_PATH", os.path.join(temporary.name, "test.db"))
        db_patch.start()
        self.addCleanup(db_patch.stop)
        database.init_db()
        self.replace_rows([("2", 20.5, 1), ("10", 10.25, 0), ("30", 30.75, 0)])
        self.tracker = api_main.create_stylus_hours_tracker()
        tracker_patch = patch.object(api_main, "stylus_hours_tracker", self.tracker)
        tracker_patch.start()
        self.addCleanup(tracker_patch.stop)
        previous_runtime = deepcopy(api_main.runtime_state)
        self.addCleanup(lambda: (api_main.runtime_state.clear(), api_main.runtime_state.update(previous_runtime)))
        api_main.runtime_state.update(status="stop", status_time=None, stylus_hours={})
        self.client = api_main.app.test_client()

    def replace_rows(self, rows):
        with sqlite3.connect(database.DB_PATH) as conn:
            conn.execute("DELETE FROM stylus")
            conn.executemany(
                "INSERT INTO stylus VALUES (?, ?, ?, ?, ?, ?)",
                [(id, f"Stylus {id}", hours, 500, 1000, active) for id, hours, active in rows],
            )

    def rows(self):
        with sqlite3.connect(database.DB_PATH) as conn:
            return conn.execute("SELECT * FROM stylus ORDER BY id").fetchall()

    def status(self, status, time=None):
        api_main.broadcast_message({"event": "status", "data": {"status": status, "time": time}})

    def tracking_state(self):
        return (self.tracker.active_stylus_id, self.tracker.current_hours,
                self.tracker.pending_seconds, self.tracker.last_elapsed_seconds)

    def post(self, id):
        with api_main.app.test_client() as client:
            return client.post(f"/styli/{id}/activate")

    def test_legacy_normalization_preserves_first_active_id_hours_and_metadata(self):
        for rows, expected in (
            ([("2", 2.25, 1), ("10", 10.5, 1), ("1", 1.75, 0)], "10"),
            ([("2", 2.25, 0), ("10", 10.5, 0), ("1", 1.75, None)], "1"),
        ):
            with self.subTest(expected=expected):
                self.replace_rows(rows)
                before = [r[:-1] for r in self.rows()]
                database.init_db()
                database.init_db()
                self.assertEqual([r[:-1] for r in self.rows()], before)
                self.assertEqual([r[0] for r in self.rows() if r[-1] == 1], [expected])

    def test_api_flags_are_boolean_and_navigation_order_does_not_follow_selection(self):
        for selected in ("2", "30", "10"):
            self.assertEqual(self.post(selected).get_json(), {"success": True})
            styli = self.client.get("/styli").get_json()
            self.assertEqual([s["id"] for s in styli], ["10", "2", "30"])
            self.assertEqual([s["id"] for s in styli if s["active"]], [selected])
            for stylus in styli:
                self.assertIs(type(stylus["active"]), bool)
                self.assertEqual(self.client.get(f"/styli/{stylus['id']}").get_json(), stylus)
        # A mock ID must not appear as active alongside a saved collection.
        self.assertEqual(self.client.get("/styli/1").status_code, 404)

    def test_mock_data_exposes_active_boolean_but_cannot_be_activated(self):
        self.replace_rows([])
        self.assertIs(self.client.get("/styli").get_json()[0]["active"], True)
        self.assertIs(self.client.get("/styli/1").get_json()["active"], True)
        self.assertEqual(self.post("1").status_code, 404)

    def test_sync_preserves_local_selection_totals_and_metadata(self):
        self.post("30")
        before = self.rows()
        database.upsert_styli([
            {"id": id, "name": "Remote metadata", "active": True, "distance_hours": 999}
            for id in ("1", "2", "10", "30")
        ])
        self.assertEqual([row for row in self.rows() if row[0] != "1"], before)
        self.assertEqual(database.get_active_stylus_hours(), {"id": "30", "hours": 30.75})
        self.assertEqual(next(s for s in database.get_all_styli() if s["id"] == "1")["hours"], 0)

    def test_first_sync_selects_first_id_and_reimport_starts_at_zero(self):
        self.replace_rows([])
        remote = [{"id": id, "name": id, "active": True, "distance_hours": 999}
                  for id in ("2", "10", "30")]
        database.upsert_styli(remote)
        self.assertEqual(database.get_active_stylus_hours(), {"id": "10", "hours": 0})
        database.set_stylus_hours("30", 123.45)
        self.assertTrue(database.delete_stylus("30"))
        database.upsert_styli(remote)
        self.assertEqual(database.get_active_stylus_hours(), {"id": "10", "hours": 0})
        self.assertTrue(all(s["hours"] == 0 for s in database.get_all_styli()))

    def test_activation_survives_real_process_restart_and_playback_counts_only_selection(self):
        response = self.post("30")
        self.assertEqual(response.status_code, 200)
        restart_check = """
import json, sys
from api.services.db import database
database.DB_PATH = sys.argv[1]
from api.main import app, create_stylus_hours_tracker
tracker = create_stylus_hours_tracker()
tracker.process_message({'event': 'status', 'data': {'status': 'play', 'time': '00:00'}})
tracker.process_message({'event': 'status', 'data': {'status': 'play', 'time': '01:00'}})
tracker.process_message({'event': 'status', 'data': {'status': 'stop'}})
print(json.dumps({'event': tracker.current_event(), 'styli': app.test_client().get('/styli').get_json()}))
"""
        result = subprocess.run(
            [sys.executable, "-c", restart_check, database.DB_PATH],
            cwd=Path(__file__).resolve().parent.parent, capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        restarted = json.loads(result.stdout)
        self.assertEqual(restarted["event"]["data"]["stylus_id"], "30")
        self.assertEqual([s["id"] for s in restarted["styli"] if s["active"]], ["30"])
        totals = {s["id"]: s["hours"] for s in restarted["styli"]}
        self.assertEqual(totals["2"], 20.5)
        self.assertEqual(totals["10"], 10.25)
        self.assertAlmostEqual(totals["30"], 30.75 + 60 / 3600)

    def test_playback_guard_leaves_all_state_unchanged_even_for_active_and_missing_ids(self):
        self.status("play", "00:00")
        self.status("play", "04:00")
        before_rows, before_tracking = self.rows(), self.tracking_state()
        before_runtime = deepcopy(api_main.runtime_state)
        for id in ("2", "30", "missing"):
            with self.subTest(id=id):
                response = self.post(id)
                self.assertEqual(response.status_code, 409)
                self.assertIn("error", response.get_json())
                self.assertEqual(self.rows(), before_rows)
                self.assertEqual(self.tracking_state(), before_tracking)
                self.assertEqual(api_main.runtime_state, before_runtime)
        self.status("stop")
        self.assertEqual(self.post("30").status_code, 200)
        self.assertEqual(self.tracker.active_stylus_id, "30")

    def test_missing_activation_is_json_404_without_tracking_or_row_changes(self):
        self.status("play", "00:00")
        self.status("stop")
        before_rows, before_tracking = self.rows(), self.tracking_state()
        response = self.post("missing")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())
        self.assertEqual(self.rows(), before_rows)
        self.assertEqual(self.tracking_state(), before_tracking)
        self.assertIsNone(database.activate_stylus("missing"))

    def test_repeated_stopped_activation_is_a_noop(self):
        self.status("play", "00:00")
        self.status("play", "00:12")
        api_main.runtime_state["status"] = "stop"  # Pending usage from an unsuccessful stop flush.
        before_rows, before_tracking = self.rows(), self.tracking_state()
        with patch.object(database, "activate_stylus") as save, patch.object(self.tracker, "flush_pending") as flush:
            self.assertEqual(self.post("2").status_code, 200)
            self.assertEqual(self.post("2").status_code, 200)
        save.assert_not_called()
        flush.assert_not_called()
        self.assertEqual(self.rows(), before_rows)
        self.assertEqual(self.tracking_state(), before_tracking)

    def test_pending_save_failure_aborts_then_success_saves_previous_before_switch(self):
        self.status("play", "00:00")
        self.status("play", "04:00")
        with patch.object(self.tracker, "increment_stylus_hours", return_value=False):
            self.status("stop")
            before = self.tracking_state()
            response = self.post("30")
            self.assertEqual(response.status_code, 500)
            self.assertIn("error", response.get_json())
            self.assertEqual(self.tracking_state(), before)
            self.assertEqual(database.get_active_stylus_hours()["id"], "2")
        original_save = database.activate_stylus

        def check_flush_then_save(id):
            self.assertEqual(self.tracker.pending_seconds, 0)
            self.assertAlmostEqual(database.get_active_stylus_hours()["hours"], 20.5 + 240 / 3600)
            return original_save(id)

        with patch.object(database, "activate_stylus", side_effect=check_flush_then_save):
            self.assertEqual(self.post("30").status_code, 200)
        self.assertEqual(self.tracking_state(), ("30", 30.75, 0, None))
        self.status("play", "10:00")
        self.status("play", "10:01")
        self.assertAlmostEqual(self.tracker.current_hours, 30.75 + 1 / 3600)

    def test_exception_during_stop_still_marks_stopped_and_preserves_pending_usage(self):
        self.status("play", "00:00")
        self.status("play", "00:05")
        with patch.object(self.tracker, "increment_stylus_hours", side_effect=sqlite3.OperationalError("disk failed")):
            self.status("stop")
            self.assertEqual(api_main.runtime_state["status"], "stop")
            self.assertEqual(self.tracker.pending_seconds, 5)
            self.assertIsNone(self.tracker.last_elapsed_seconds)
            self.assertEqual(self.post("30").status_code, 500)
        self.assertEqual(self.post("30").status_code, 200)

    def test_selection_write_failure_returns_json_500_and_rolls_back_flags(self):
        self.status("play", "00:00")
        self.status("stop")
        before_rows, before_tracking = self.rows(), self.tracking_state()
        with sqlite3.connect(database.DB_PATH) as conn:
            conn.executescript("""
                CREATE TRIGGER reject_selection BEFORE UPDATE OF active ON stylus
                WHEN OLD.active != NEW.active
                BEGIN SELECT RAISE(ABORT, 'selection refused'); END;
            """)
        response = self.post("30")
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.get_json())
        self.assertEqual(self.rows(), before_rows)
        self.assertEqual(self.tracking_state(), before_tracking)

    def test_selection_commit_failure_rolls_back_before_success(self):
        original_connection = database._get_connection

        def reject_commit(**kwargs):
            conn = original_connection(**kwargs)
            conn.set_authorizer(lambda action, first, *_: sqlite3.SQLITE_DENY
                                if action == sqlite3.SQLITE_TRANSACTION and first == "COMMIT"
                                else sqlite3.SQLITE_OK)
            return conn

        original_save = database.activate_stylus

        def save(id):
            with patch.object(database, "_get_connection", side_effect=reject_commit):
                return original_save(id)

        before = self.rows()
        with patch.object(database, "activate_stylus", side_effect=save):
            response = self.post("30")
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.get_json())
        self.assertEqual(self.rows(), before)
        self.assertEqual(self.tracking_state(), (None, None, 0, None))

    def test_failed_selection_after_successful_flush_does_not_lose_or_duplicate_usage(self):
        self.status("play", "00:00")
        self.status("play", "00:12")
        with patch.object(self.tracker, "increment_stylus_hours", return_value=False):
            self.status("stop")
        with patch.object(database, "activate_stylus", side_effect=sqlite3.OperationalError("selection failed")):
            self.assertEqual(self.post("30").status_code, 500)
        previous_hours = 20.5 + 12 / 3600
        self.assertEqual(database.get_active_stylus_hours()["id"], "2")
        self.assertAlmostEqual(database.get_active_stylus_hours()["hours"], previous_hours)
        self.assertEqual(self.tracking_state(), ("2", previous_hours, 0, None))
        self.assertEqual(self.post("30").status_code, 200)
        self.assertAlmostEqual(next(s["hours"] for s in database.get_all_styli() if s["id"] == "2"), previous_hours)
        self.assertEqual(self.tracking_state(), ("30", 30.75, 0, None))

    def test_playback_cannot_start_between_guard_and_selection_commit(self):
        in_save, allow_save, play_attempted = threading.Event(), threading.Event(), threading.Event()
        original_save = database.activate_stylus
        lock_blocked = []

        def paused_save(id):
            in_save.set()
            if not allow_save.wait(5):
                raise TimeoutError("Test did not release save")
            self.assertEqual(api_main.runtime_state["status"], "stop")
            return original_save(id)

        def start_play():
            acquired = self.tracker.lock.acquire(blocking=False)
            lock_blocked.append(not acquired)
            if acquired:
                self.tracker.lock.release()
            play_attempted.set()
            self.status("play", "00:00")

        with ThreadPoolExecutor(max_workers=2) as workers, patch.object(database, "activate_stylus", side_effect=paused_save):
            activation = workers.submit(self.post, "30")
            try:
                self.assertTrue(in_save.wait(3))
                playback = workers.submit(start_play)
                self.assertTrue(play_attempted.wait(3))
                self.assertEqual(lock_blocked, [True])
                self.assertEqual(api_main.runtime_state["status"], "stop")
                self.assertFalse(playback.done())
            finally:
                allow_save.set()
            self.assertEqual(activation.result(5).status_code, 200)
            playback.result(5)
        self.assertEqual(api_main.runtime_state["status"], "play")
        self.assertEqual(self.tracker.active_stylus_id, "30")
        self.assertEqual(self.post("2").status_code, 409)

    def test_playback_winning_race_rejects_activation_before_any_persistence(self):
        in_play, allow_play, activation_attempted = threading.Event(), threading.Event(), threading.Event()
        original_process = self.tracker.process_message

        def paused_play(message):
            in_play.set()
            if not allow_play.wait(5):
                raise TimeoutError("Test did not release playback")
            return original_process(message)

        def activate():
            activation_attempted.set()
            return self.post("30")

        with ThreadPoolExecutor(max_workers=2) as workers, patch.object(self.tracker, "process_message", side_effect=paused_play):
            playback = workers.submit(self.status, "play", "00:00")
            try:
                self.assertTrue(in_play.wait(3))
                activation = workers.submit(activate)
                self.assertTrue(activation_attempted.wait(3))
                self.assertFalse(activation.done())
            finally:
                allow_play.set()
            playback.result(5)
            self.assertEqual(activation.result(5).status_code, 409)
        self.assertEqual(database.get_active_stylus_hours()["id"], "2")


if __name__ == "__main__":
    unittest.main()

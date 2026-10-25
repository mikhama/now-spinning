import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from api.services.db import database
from api.session_history import SessionHistoryTracker


START = datetime(2026, 10, 25, 10, tzinfo=timezone.utc)


class SessionHistoryDatabaseTestCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.db_patch = patch.object(database, "DB_PATH", os.path.join(directory.name, "history.db"))
        self.db_patch.start()
        self.addCleanup(self.db_patch.stop)
        database.init_db()

    def test_additive_initialization_and_sync_preserve_all_existing_data(self):
        with sqlite3.connect(database.DB_PATH) as conn:
            conn.execute("DROP TABLE sessions_log")
            conn.execute("INSERT INTO record VALUES ('A','r','m','Album','Artist','[]',1)")
            conn.execute("INSERT INTO stylus VALUES ('1','Stylus',123.45,500,1000,1)")
            conn.execute("INSERT INTO status VALUES ('2026-10-24')")
        before = self.other_tables()
        database.init_db()
        database.init_db()
        self.assertEqual(self.other_tables(), before)
        with sqlite3.connect(database.DB_PATH) as conn:
            columns = conn.execute("PRAGMA table_info(sessions_log)").fetchall()
        self.assertEqual([(c[1], c[2], c[5]) for c in columns], [
            ("id", "INTEGER", 1), ("record_id", "TEXT", 0),
            ("session_started_at", "TEXT", 0), ("session_duration_sec", "INTEGER", 0),
        ])
        database.save_playback_sessions([("A", START.isoformat(), 12)])
        before_history = database.get_playback_sessions()
        database.init_db()
        database.upsert_styli([{"id": "1", "name": "Remote", "distance_hours": 999}])
        database.upsert_records([dict(id="A", release_id="r", master_id="m", title="Album", artist="Artist", sides=[])])
        database.update_sync_date()
        self.assertEqual(database.get_playback_sessions(), before_history)
        self.assertEqual(database.get_active_stylus_hours()["hours"], 123.45)

    def other_tables(self):
        with sqlite3.connect(database.DB_PATH) as conn:
            return {table: conn.execute(f"SELECT * FROM {table}").fetchall() for table in ("record", "stylus", "status")}

    def test_schema_rejects_empty_record_and_nonpositive_or_fractional_durations(self):
        for id, seconds in (("", 1), (" ", 1), ("A", 0), ("A", -1), ("A", 1.5), ("A", None)):
            with self.subTest(id=id, seconds=seconds), self.assertRaises(sqlite3.IntegrityError):
                database.save_playback_sessions([(id, START.isoformat(), seconds)])
        self.assertEqual(database.get_playback_sessions(), [])

    def test_failed_batch_rolls_back_earlier_rows_and_retry_saves_once(self):
        rows = [("A", START.isoformat(), 12), ("B", START.isoformat(), 34)]
        with sqlite3.connect(database.DB_PATH) as conn:
            conn.execute("""CREATE TRIGGER fail_second BEFORE INSERT ON sessions_log
                            WHEN NEW.record_id = 'B' BEGIN SELECT RAISE(ABORT, 'disk failed'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            database.save_playback_sessions(rows)
        self.assertEqual(database.get_playback_sessions(), [])
        with sqlite3.connect(database.DB_PATH) as conn:
            conn.execute("DROP TRIGGER fail_second")
        self.assertTrue(database.save_playback_sessions(rows))
        self.assertEqual([r["session_duration_sec"] for r in database.get_playback_sessions()], [12, 34])

    def test_commit_failure_rolls_back_inserts_and_clear(self):
        database.save_playback_sessions([("A", START.isoformat(), 12)])
        original = database._get_connection

        def reject_commit(**kwargs):
            conn = original(**kwargs)
            conn.set_authorizer(lambda action, first, *_: sqlite3.SQLITE_DENY
                                if action == sqlite3.SQLITE_TRANSACTION and first == "COMMIT"
                                else sqlite3.SQLITE_OK)
            return conn

        before = database.get_playback_sessions()
        for operation in (lambda: database.save_playback_sessions([("B", START.isoformat(), 4)]), database.clear_playback_sessions):
            with patch.object(database, "_get_connection", side_effect=reject_commit):
                with self.assertRaises(sqlite3.DatabaseError):
                    operation()
            self.assertEqual(database.get_playback_sessions(), before)

    def test_report_reads_only_committed_rows_while_writer_is_open(self):
        database.save_playback_sessions([("A", START.isoformat(), 12)])
        conn = database._get_connection()
        try:
            conn.execute("INSERT INTO sessions_log VALUES (2,'B',?,34)", (START.isoformat(),))
            self.assertEqual([r["record_id"] for r in database.get_playback_sessions()], ["A"])
            conn.commit()
            self.assertEqual([r["record_id"] for r in database.get_playback_sessions()], ["A", "B"])
        finally:
            conn.close()

    def test_local_record_lookup_requires_existing_nonempty_id(self):
        with sqlite3.connect(database.DB_PATH) as conn:
            conn.execute("INSERT INTO record (id) VALUES ('1')")
        self.assertTrue(database.record_exists("1"))
        self.assertTrue(database.record_exists(1))
        for value in (None, "", " ", "missing"):
            self.assertFalse(database.record_exists(value))


class SessionHistoryTrackerTestCase(unittest.TestCase):
    def setUp(self):
        self.known = {"A", "B"}
        self.saved = []
        self.wall = START
        self.tracker = SessionHistoryTracker(lambda id: id in self.known, self.save, now=lambda: self.wall)

    def save(self, rows):
        self.saved.extend(rows)
        return True

    def play(self, elapsed, record="A", *, wall=None):
        self.wall = wall or START + timedelta(seconds=elapsed)
        self.tracker.process_message(
            {"event": "status", "data": {"status": "play", "time": f"{elapsed // 60:02}:{elapsed % 60:02}"}}, record,
        )

    def stop(self, record="A"):
        self.tracker.process_message({"event": "status", "data": {"status": "stop"}}, record)
        return self.tracker.flush_pending()

    def test_first_counted_interval_and_checkpoint_advance_the_start(self):
        self.play(1000)
        self.play(1600)
        self.assertTrue(self.tracker.checkpoint_due)
        self.assertTrue(self.tracker.flush_pending())
        self.assertEqual(self.saved, [("A", (START + timedelta(seconds=1000)).isoformat(), 600)])
        # Observation latency must not move the start of an already-open segment.
        self.play(1634, wall=START + timedelta(days=1))
        self.stop()
        self.assertEqual(self.saved[-1], ("A", (START + timedelta(seconds=1600)).isoformat(), 34))
        self.assertEqual(self.tracker.pending_seconds, 0)

    def test_short_session_stop_resume_excludes_the_gap(self):
        self.play(0)
        self.play(12)
        self.stop()
        self.play(12, wall=START + timedelta(days=30))
        self.play(17, wall=START + timedelta(days=30, seconds=5))
        self.stop()
        self.stop()
        self.assertEqual(self.saved, [("A", START.isoformat(), 12), ("A", (START + timedelta(days=30)).isoformat(), 5)])

    def test_empty_unresolved_and_later_resolved_records_never_back_count(self):
        for record in (None, "", " ", "missing"):
            self.play(0, record)
            self.play(120, record)
            self.stop(record)
        self.assertEqual(self.saved, [])
        self.play(200, "missing")
        self.known.add("missing")
        self.play(201, "missing")
        self.assertEqual(self.tracker.pending_seconds, 0)
        self.play(205, "missing")
        self.stop("missing")
        self.assertEqual(self.saved, [("missing", (START + timedelta(seconds=201)).isoformat(), 4)])

    def test_record_change_closes_previous_before_new_counter_baseline(self):
        self.play(0)
        self.play(10)
        self.tracker.process_message({"event": "current_record", "data": {"record_id": "B"}}, "B")
        self.assertTrue(self.tracker.checkpoint_due)
        self.play(20, "B")
        self.play(25, "B")
        self.stop("B")
        self.assertEqual([r[::2] for r in self.saved], [("A", 10), ("B", 5)])

    def test_counter_reset_closes_previous_and_starts_a_new_segment(self):
        self.play(0)
        self.play(10)
        self.play(0, wall=START + timedelta(seconds=20))
        self.play(3, wall=START + timedelta(seconds=23))
        self.stop()
        self.assertEqual(self.saved, [("A", START.isoformat(), 10), ("A", (START + timedelta(seconds=20)).isoformat(), 3)])

    def test_failures_keep_multiple_segments_in_order_until_commit_then_retry_is_empty(self):
        callback = Mock(side_effect=sqlite3.OperationalError("write failed"))
        self.tracker.save_sessions = callback
        for index, record in enumerate(("A", "B", "A")):
            self.play(0, record, wall=START + timedelta(minutes=index))
            self.play(10, record, wall=START + timedelta(minutes=index, seconds=10))
            with self.assertRaises(sqlite3.OperationalError):
                self.stop(record)
        self.assertEqual(self.tracker.pending_seconds, 30)
        self.assertEqual([r[0] for r in callback.call_args.args[0]], ["A", "B", "A"])
        self.tracker.save_sessions = self.save
        self.assertTrue(self.tracker.flush_pending())
        self.assertTrue(self.tracker.flush_pending())
        self.assertEqual([r[0] for r in self.saved], ["A", "B", "A"])
        self.assertEqual(self.tracker.pending_seconds, 0)

    def test_false_save_retains_start_and_all_seconds_for_later_retry(self):
        self.play(0)
        self.play(600)
        self.tracker.save_sessions = Mock(return_value=False)
        self.assertFalse(self.tracker.flush_pending())
        self.play(634)
        self.tracker.save_sessions = self.save
        self.stop()
        self.assertEqual(self.saved, [("A", START.isoformat(), 634)])

    def test_lookup_failure_closes_old_record_and_prevents_later_misattribution(self):
        self.play(0)
        self.play(10)
        with patch.object(self.tracker, "record_exists", side_effect=sqlite3.OperationalError("lookup failed")):
            with self.assertRaises(sqlite3.OperationalError):
                self.play(20, "B")
        self.play(30, "B")
        self.play(31, "B")
        self.stop("B")
        self.assertEqual([r[::2] for r in self.saved], [("A", 10), ("B", 1)])

    def test_invalid_counter_and_duplicate_observation_add_no_seconds(self):
        self.play(0)
        for time in ("bad", "00:60", None):
            self.tracker.process_message({"event": "status", "data": {"status": "play", "time": time}}, "A")
        self.play(0)
        self.stop()
        self.assertEqual(self.saved, [])


if __name__ == "__main__":
    unittest.main()

from contextlib import redirect_stderr, redirect_stdout
from datetime import timezone
import io
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from api.services.db import database
from api.sessions_history_cli import CONFIRMATION, combine_sessions, display_width, main, render_report


class SessionsHistoryCliTestCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        db_patch = patch.object(database, "DB_PATH", os.path.join(directory.name, "history.db"))
        db_patch.start()
        self.addCleanup(db_patch.stop)
        database.init_db()
        with sqlite3.connect(database.DB_PATH) as conn:
            conn.executemany("INSERT INTO record (id,title,artist) VALUES (?,?,?)", [("A", "Żółć 東京", "坂本 龍一"), ("B", "Second album", "坂本 龍一")])
            conn.execute("INSERT INTO stylus VALUES ('1','Stylus',123.45,500,1000,1)")
            conn.execute("INSERT INTO status VALUES ('2026-10-25')")

    def invoke(self, argv=None, response=None, error=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr), patch("builtins.input", return_value=response, side_effect=error):
            code = main(argv or [])
        return code, stdout.getvalue(), stderr.getvalue()

    def save(self, record, start, seconds):
        database.save_playback_sessions([(record, start, seconds)])

    def other_tables(self):
        with sqlite3.connect(database.DB_PATH) as conn:
            return [conn.execute(f"SELECT * FROM {table}").fetchall() for table in ("record", "stylus", "status")]

    def test_example_totals_are_1234_and_245_seconds_despite_large_gaps(self):
        # The request supplies totals but no source rows; these explicit entries
        # define the reproducible example, including gaps of several months.
        rows = [
            ("A", "2026-01-01T10:00:00+00:00", 600),
            ("A", "2026-04-01T10:00:00+00:00", 600),
            ("A", "2026-10-01T10:00:00+00:00", 34),
            ("B", "2026-10-02T10:00:00+00:00", 120),
            ("B", "2026-10-24T10:00:00+00:00", 125),
        ]
        database.save_playback_sessions(list(reversed(rows)))
        combined = combine_sessions(database.get_playback_sessions())
        self.assertEqual([r["session_duration_sec"] for r in combined], [1234, 245])
        self.assertEqual(combined[0]["session_started_at"], rows[0][1])
        code, report, stderr = self.invoke()
        self.assertEqual((code, stderr), (0, ""))
        self.assertIn("00:20:34", report)
        self.assertIn("00:04:05", report)
        self.assertEqual(len(report.splitlines()), 3)

    def test_a_b_a_remains_three_rows_in_chronological_then_primary_key_order(self):
        self.save("A", "2026-10-25T11:00:00+00:00", 1)
        self.save("B", "2026-10-25T10:00:00+00:00", 2)
        self.save("A", "2026-10-25T10:00:00+00:00", 3)
        self.save("A", "2026-10-25T09:00:00+00:00", 4)
        entries = database.get_playback_sessions()
        self.assertEqual([r["id"] for r in entries], [4, 2, 3, 1])
        self.assertEqual([(r["record_id"], r["session_duration_sec"]) for r in combine_sessions(entries)], [("A", 4), ("B", 2), ("A", 4)])

    def test_report_converts_each_timestamp_with_the_correct_dst_offset(self):
        self.save("A", "2026-10-25T00:30:00+00:00", 1)
        self.save("B", "2026-10-25T01:30:00+00:00", 2)
        report = render_report(database.get_playback_sessions(), local_timezone=ZoneInfo("Europe/Warsaw"))
        self.assertIn("2026-10-25 02:30:00+02:00", report)
        self.assertIn("2026-10-25 02:30:00+01:00", report)

    def test_default_report_uses_system_local_timezone(self):
        self.save("A", "2026-07-01T10:00:00+00:00", 12)
        result = self.subprocess_command([], env={**os.environ, "TZ": "Europe/Warsaw"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("2026-07-01 12:00:00+02:00", result.stdout)

    def test_full_duration_and_readable_unicode_are_aligned(self):
        self.save("A", "2026-10-24T10:00:00+00:00", 90061)
        self.save("B", "2026-10-25T10:00:00+00:00", 2)
        report = render_report(database.get_playback_sessions(), local_timezone=timezone.utc)
        self.assertIn("25:01:01", report)
        lines = report.splitlines()
        self.assertIn("坂本 龍一", lines[1])
        self.assertIn("Żółć 東京", lines[1])
        album_positions = [display_width(lines[0][:lines[0].index("Album")]),
                           display_width(lines[1][:lines[1].index("Żółć")]),
                           display_width(lines[2][:lines[2].index("Second album")])]
        self.assertEqual(len(set(album_positions)), 1)
        self.assertEqual(display_width("e\u0301東京"), 5)

    def test_metadata_disappearance_preserves_history_with_id_and_fallback(self):
        self.save("A", "2026-10-25T10:00:00+00:00", 12)
        with sqlite3.connect(database.DB_PATH) as conn:
            conn.execute("DELETE FROM record WHERE id = 'A'")
        code, report, _ = self.invoke()
        self.assertEqual(code, 0)
        self.assertIn("Unknown", report)
        self.assertIn("00:00:12", report)
        self.assertTrue(report.splitlines()[1].endswith("A"))

    def test_empty_report_has_required_columns_and_clear_preserves_other_tables(self):
        code, report, _ = self.invoke()
        self.assertEqual(code, 0)
        for title in ("Started at", "Duration", "Artist", "Album", "Album ID"):
            self.assertIn(title, report)
        self.assertIn("No saved playback history", report)
        self.save("A", "2026-10-25T10:00:00+00:00", 12)
        before = self.other_tables()
        code, output, stderr = self.invoke(["clear"], CONFIRMATION)
        self.assertEqual((code, stderr), (0, ""))
        self.assertIn("Playback history cleared.", output)
        self.assertEqual(database.get_playback_sessions(), [])
        self.assertEqual(self.other_tables(), before)

    def test_only_exact_confirmation_is_accepted_and_eof_or_interruption_cancel(self):
        self.save("A", "2026-10-25T10:00:00+00:00", 12)
        before = database.get_playback_sessions()
        for response in ("", "yes", "YES I HEREBY CONFIRM", " " + CONFIRMATION, CONFIRMATION + " "):
            with self.subTest(response=response):
                code, output, _ = self.invoke(["clear"], response)
                self.assertEqual(code, 0)
                self.assertIn("Cancelled", output)
                self.assertEqual(database.get_playback_sessions(), before)
        for error in (EOFError(), KeyboardInterrupt()):
            code, output, _ = self.invoke(["clear"], error=error)
            self.assertEqual(code, 0)
            self.assertIn("Cancelled", output)
            self.assertEqual(database.get_playback_sessions(), before)

    def test_clear_commit_failure_reports_error_without_success_and_rolls_back(self):
        self.save("A", "2026-10-25T10:00:00+00:00", 12)
        before = database.get_playback_sessions(), self.other_tables()
        original = database._get_connection

        def reject_commit(**kwargs):
            conn = original(**kwargs)
            conn.set_authorizer(lambda action, first, *_: sqlite3.SQLITE_DENY
                                if action == sqlite3.SQLITE_TRANSACTION and first == "COMMIT" else sqlite3.SQLITE_OK)
            return conn

        with patch.object(database, "_get_connection", side_effect=reject_commit):
            code, output, stderr = self.invoke(["clear"], CONFIRMATION)
        self.assertEqual(code, 1)
        self.assertNotIn("Playback history cleared.", output)
        self.assertIn("Error:", stderr)
        self.assertEqual((database.get_playback_sessions(), self.other_tables()), before)

    def test_missing_database_is_never_created_by_either_command(self):
        missing = database.DB_PATH + ".missing"
        with patch.object(database, "DB_PATH", missing):
            for args in ([], ["clear"]):
                code, output, stderr = self.invoke(args, CONFIRMATION)
                self.assertEqual(code, 1)
                self.assertIn("Error:", stderr)
                self.assertFalse(os.path.exists(missing))
                self.assertNotIn("Playback history cleared.", output)

    def test_legacy_schema_is_never_upgraded_by_either_command(self):
        with sqlite3.connect(database.DB_PATH) as conn:
            conn.execute("DROP TABLE sessions_log")
        before = self.other_tables()
        for args in ([], ["clear"]):
            code, _, stderr = self.invoke(args, CONFIRMATION)
            self.assertEqual(code, 1)
            self.assertIn("sessions_log", stderr)
        with sqlite3.connect(database.DB_PATH) as conn:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        self.assertEqual(tables, {"record", "stylus", "status"})
        self.assertEqual(self.other_tables(), before)

    def subprocess_command(self, args, *, input=None, env=None):
        root = Path(__file__).resolve().parents[1]
        runner = """
import runpy, sys
from api.services.db import database
database.DB_PATH = sys.argv.pop(1)
runpy.run_path('bin/sessions-history', run_name='__main__')
"""
        return subprocess.run([sys.executable, "-S", "-c", runner, database.DB_PATH, *args], cwd=root,
                              input=input, capture_output=True, text=True, timeout=10, env=env)

    def test_actual_command_works_without_site_packages_for_report_and_clear(self):
        self.save("A", "2026-10-25T10:00:00+00:00", 12)
        report = self.subprocess_command([])
        self.assertEqual(report.returncode, 0, report.stderr)
        self.assertIn("坂本 龍一", report.stdout)
        cancelled = self.subprocess_command(["clear"], input="yes\n")
        self.assertEqual(cancelled.returncode, 0, cancelled.stderr)
        self.assertEqual(len(database.get_playback_sessions()), 1)
        cleared = self.subprocess_command(["clear"], input=CONFIRMATION + "\n")
        self.assertEqual(cleared.returncode, 0, cleared.stderr)
        self.assertIn('Type exactly "yes I hereby confirm"', cleared.stdout)
        self.assertIn("Playback history cleared.", cleared.stdout)
        self.assertEqual(database.get_playback_sessions(), [])

    def test_executable_and_subcommand_help_document_procedure(self):
        command = Path(__file__).resolve().parents[1] / "bin" / "sessions-history"
        self.assertTrue(os.access(command, os.X_OK))
        for args in (["--help"], ["clear", "--help"]):
            result = subprocess.run([str(command), *args], cwd="/private/tmp", capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            for phrase in ("wait until it has stopped", "saved history only", "Collection sync preserves", "record.id"):
                self.assertIn(phrase, " ".join(result.stdout.split()))


if __name__ == "__main__":
    unittest.main()

import io
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from api.services.db import database
from api.stylus_hours_cli import main


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class StylusHoursCliTestCase(unittest.TestCase):
    def setUp(self):
        # A disposable project exercises the actual executable without touching
        # the developer's database. Special characters also exercise URI quoting.
        temporary = tempfile.TemporaryDirectory(prefix="stylus-hours ?# ")
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)
        for relative in (
            "bin/stylus-hours",
            "api/__init__.py",
            "api/stylus_hours_cli.py",
            "api/services/__init__.py",
            "api/services/db/__init__.py",
            "api/services/db/database.py",
        ):
            destination = self.project / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PROJECT_ROOT / relative, destination)

        self.db_path = self.project / "data" / "now-spinning.db"
        db_patch = patch.object(database, "DB_PATH", str(self.db_path))
        db_patch.start()
        self.addCleanup(db_patch.stop)
        database.init_db()
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                "INSERT INTO stylus VALUES (?, ?, ?, ?, ?, ?)",
                [("1", "First stylus", 102.4, 500, 1000, 1),
                 ("2", "Другой stylus", 25.5, 300, 800, 0)],
            )

    def rows(self):
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT * FROM stylus ORDER BY id").fetchall()

    def command(self, *arguments, without_site=False):
        script = str(self.project / "bin" / "stylus-hours")
        invocation = [sys.executable, "-S", script] if without_site else [script]
        return subprocess.run(
            invocation + list(arguments),
            cwd=self.project,
            capture_output=True,
            text=True,
            timeout=15,
        )

    def assert_failed(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("error", result.stderr.lower())
        self.assertNotIn("Traceback", result.stderr)

    def test_executable_lists_every_stylus_without_modifying_totals(self):
        before = self.rows()
        self.assertTrue(os.access(self.project / "bin/stylus-hours", os.X_OK))

        result = self.command("list")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertIn("1\tFirst stylus\t102.4", result.stdout)
        self.assertIn("2\tДругой stylus\t25.5", result.stdout)
        self.assertEqual(self.rows(), before)

    def test_list_empty_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM stylus")
        result = self.command("list")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No styli", result.stdout)

    def test_set_replaces_exact_total_and_reports_previous_and_new(self):
        before = self.rows()
        result = self.command("set", "1", "97.3")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "Stylus 1: 102.4 hours -> 97.3 hours\n")
        self.assertEqual(self.rows()[0], before[0][:2] + (97.3,) + before[0][3:])
        self.assertEqual(self.rows()[1], before[1])

    def test_set_keeps_precision_accepts_zero_and_is_not_additive(self):
        for hours in ("97.3123456789", "0", "1e100", "97.3123456789"):
            with self.subTest(hours=hours):
                result = self.command("set", "1", hours)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.rows()[0][2], float(hours))
                self.assertIn(f"-> {float(hours)} hours", result.stdout)

    def test_reset_saves_zero_and_reports_change(self):
        result = self.command("reset", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "Stylus 1: 102.4 hours -> 0.0 hours\n")
        self.assertEqual(self.rows()[0][2], 0)
        self.assertEqual(self.rows()[1][2], 25.5)

    def test_commands_run_without_site_packages(self):
        # -S removes third-party site packages; api.main is not even copied.
        for arguments in (("list",), ("set", "1", "97.3"), ("reset", "1"), ("delete", "2")):
            with self.subTest(arguments=arguments):
                result = self.command(*arguments, without_site=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_hours_leave_all_rows_unchanged(self):
        before = self.rows()
        for hours in ("-1", "-0.01", "nan", "NaN", "inf", "-inf", "Infinity", "1e309", "abc", ""):
            with self.subTest(hours=hours):
                self.assert_failed(self.command("set", "1", hours))
                self.assertEqual(self.rows(), before)

    def test_missing_stylus_does_not_change_rows(self):
        before = self.rows()
        for arguments in (("set", "999", "97.3"), ("reset", "999"),
                          ("delete", "999"), ("delete", "1' OR 1=1 --"),
                          ("set", "1' OR 1=1 --", "97.3")):
            with self.subTest(arguments=arguments):
                result = self.command(*arguments)
                self.assert_failed(result)
                self.assertIn("does not exist", result.stderr)
                self.assertEqual(self.rows(), before)

    def test_missing_database_is_never_created(self):
        shutil.rmtree(self.db_path.parent)
        for arguments in (("list",), ("set", "1", "97.3"), ("reset", "1"), ("delete", "2")):
            with self.subTest(arguments=arguments):
                result = self.command(*arguments)
                self.assert_failed(result)
                self.assertIn(str(self.db_path), result.stderr)
                self.assertFalse(self.db_path.parent.exists())

    def test_existing_empty_database_is_not_initialized(self):
        self.db_path.unlink()
        self.db_path.touch()
        for arguments in (("list",), ("set", "1", "97.3"), ("reset", "1"), ("delete", "2")):
            with self.subTest(arguments=arguments):
                self.assert_failed(self.command(*arguments))
        with sqlite3.connect(self.db_path) as conn:
            self.assertEqual(conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall(), [])

    def test_bad_arguments_fail_without_changing_rows(self):
        before = self.rows()
        for arguments in ((), ("unknown",), ("set", "1"), ("reset",), ("delete",), ("list", "extra")):
            with self.subTest(arguments=arguments):
                self.assert_failed(self.command(*arguments))
                self.assertEqual(self.rows(), before)

    def test_help_explains_stopped_app_and_no_application_lock(self):
        for arguments in (("--help",), ("list", "--help"), ("set", "--help"), ("reset", "--help"), ("delete", "--help")):
            with self.subTest(arguments=arguments):
                result = self.command(*arguments)
                self.assertEqual(result.returncode, 0, result.stderr)
                text = " ".join(result.stdout.split())
                self.assertIn("Exit the app normally", text)
                self.assertIn("wait until it has stopped", text)
                self.assertIn("no application lock", text)
                self.assertIn("stylus-hours delete 2", text)
                self.assertIn("playback is stopped", text)
                self.assertIn("Deletion is local only", text)
                self.assertIn("zero hours", text)

    def test_write_failure_returns_failure_without_success_output(self):
        before = self.rows()
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TRIGGER reject_hours BEFORE UPDATE OF distance_hours ON stylus
                BEGIN SELECT RAISE(ABORT, 'save refused'); END;
            """)
        for arguments in (("set", "1", "97.3"), ("reset", "1")):
            with self.subTest(arguments=arguments):
                result = self.command(*arguments)
                self.assert_failed(result)
                self.assertIn("save refused", result.stderr)
                self.assertEqual(self.rows(), before)

    def test_commit_failure_rolls_back_and_does_not_report_success(self):
        before = self.rows()
        original_connection = database._get_connection
        attempted_commits = []

        def reject_commit(**kwargs):
            conn = original_connection(**kwargs)

            def authorize(action, first, second, db_name, source):
                if action == sqlite3.SQLITE_TRANSACTION and first == "COMMIT":
                    attempted_commits.append(first)
                    return sqlite3.SQLITE_DENY
                return sqlite3.SQLITE_OK

            conn.set_authorizer(authorize)
            return conn

        for arguments in (("set", "1", "97.3"), ("reset", "1"), ("delete", "2")):
            with self.subTest(arguments=arguments):
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch.object(database, "_get_connection", side_effect=reject_commit):
                    with redirect_stdout(stdout), redirect_stderr(stderr):
                        status = main(arguments)
                self.assertEqual(status, 1)
                self.assertEqual(stdout.getvalue(), "")
                self.assertIn("not authorized", stderr.getvalue())
                self.assertEqual(self.rows(), before)
        self.assertEqual(len(attempted_commits), 3)

    def test_delete_inactive_entry_preserves_other_rows_and_reports_after_commit(self):
        before = self.rows()
        result = self.command("delete", "2")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "Deleted stylus 2\n")
        self.assertEqual(result.stderr, "")
        self.assertEqual(self.rows(), [before[0]])
        self.assertFalse(database.delete_stylus("2"))

    def test_delete_active_stylus_raises_value_error_and_cli_fails(self):
        before = self.rows()
        with self.assertRaisesRegex(ValueError, "is active"):
            database.delete_stylus("1")
        result = self.command("delete", "1")
        self.assert_failed(result)
        self.assertIn("is active", result.stderr)
        self.assertEqual(self.rows(), before)

    def test_delete_write_failure_rolls_back_without_success(self):
        before = self.rows()
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TRIGGER reject_delete BEFORE DELETE ON stylus
                BEGIN SELECT RAISE(ABORT, 'delete refused'); END;
            """)
        result = self.command("delete", "2")
        self.assert_failed(result)
        self.assertIn("delete refused", result.stderr)
        self.assertEqual(self.rows(), before)

    def test_delete_checks_selection_and_mutates_in_one_existing_database_transaction(self):
        statements = []
        original_connection = database._get_connection

        def trace_connection(**kwargs):
            self.assertEqual(kwargs, {"existing_only": True})
            conn = original_connection(**kwargs)
            conn.set_trace_callback(statements.append)
            return conn

        with patch.object(database, "_get_connection", side_effect=trace_connection) as connect:
            self.assertTrue(database.delete_stylus("2"))
        connect.assert_called_once()
        self.assertEqual(statements[0], "BEGIN IMMEDIATE")
        self.assertEqual(statements[-1], "COMMIT")
        self.assertTrue(any("active = 1" in sql for sql in statements[1:-1]))
        self.assertTrue(any(sql.startswith("DELETE FROM stylus") for sql in statements[1:-1]))

    def test_delete_protects_effective_legacy_selection_without_normalizing_on_rejection(self):
        for flags in ((0, 0), (1, 1), (None, 0)):
            with self.subTest(flags=flags):
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("UPDATE stylus SET active = ? WHERE id = '1'", (flags[0],))
                    conn.execute("UPDATE stylus SET active = ? WHERE id = '2'", (flags[1],))
                before = self.rows()
                with self.assertRaises(ValueError):
                    database.delete_stylus("1")
                self.assertEqual(self.rows(), before)

    def test_shared_set_and_reset_report_results_and_missing_rows(self):
        self.assertEqual(database.set_stylus_hours("1", 97.3), (102.4, 97.3))
        self.assertIsNone(database.set_stylus_hours("999", 97.3))
        self.assertTrue(database.reset_stylus_hours("1"))
        self.assertTrue(database.reset_stylus_hours("1"))
        self.assertFalse(database.reset_stylus_hours("999"))
        self.assertEqual(self.rows()[0][2], 0)

    def test_shared_operation_rejects_invalid_values(self):
        before = self.rows()
        for hours in (-1, float("nan"), float("inf"), float("-inf"), "bad", None, 10**400):
            with self.subTest(hours=hours):
                with self.assertRaisesRegex(ValueError, "finite and zero or more"):
                    database.set_stylus_hours("1", hours)
                self.assertEqual(self.rows(), before)


if __name__ == "__main__":
    unittest.main()

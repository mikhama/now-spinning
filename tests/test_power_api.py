import os
import signal
import subprocess
import unittest
from contextlib import ExitStack
from unittest.mock import Mock, patch

import api.main as api_main
from api.stylus_hours import StylusHoursTracker


class PowerApiTestCase(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.dict(os.environ, {
            "BOARDLESS_MODE": "false", "KIOSK_SHUTDOWN_ENABLED": "true",
        }))
        self.stack.enter_context(patch("api.main.sys.platform", "linux"))
        self.run = self.stack.enter_context(patch("api.main.subprocess.run"))
        self.timer = self.stack.enter_context(patch("api.main.threading.Timer"))
        self.kill = self.stack.enter_context(patch("api.main.os.kill"))
        self.real_flush = api_main.flush_pending_stylus_usage
        self.flush = self.stack.enter_context(patch("api.main.flush_pending_stylus_usage"))
        self.client = api_main.app.test_client()

    def test_shutdown_gates_reject_without_persistence_or_processes(self):
        cases = [
            ({"KIOSK_SHUTDOWN_ENABLED": "false"}, "linux", "127.0.0.1"),
            ({"KIOSK_SHUTDOWN_ENABLED": "1"}, "linux", "127.0.0.1"),
            ({"BOARDLESS_MODE": "TRUE"}, "linux", "127.0.0.1"),
            ({}, "darwin", "127.0.0.1"),
            ({}, "win32", "127.0.0.1"),
            ({}, "linux", "192.168.1.20"),
            ({}, "linux", "localhost"),
            ({}, "linux", ""),
        ]
        for env, platform, address in cases:
            with self.subTest(env=env, platform=platform, address=address):
                with patch.dict(os.environ, env), patch("api.main.sys.platform", platform):
                    response = self.client.post("/shutdown", environ_overrides={"REMOTE_ADDR": address},
                                                headers={"X-Forwarded-For": "127.0.0.1"})
                self.assertEqual(response.status_code, 403)
                self.assertIn("error", response.get_json())
        self.flush.assert_not_called()
        self.run.assert_not_called()
        self.timer.assert_not_called()
        self.kill.assert_not_called()

    def test_shutdown_flushes_before_fixed_bounded_command_for_loopback(self):
        for address in ("127.0.0.1", "127.0.0.2", "::1"):
            with self.subTest(address=address):
                calls = Mock()
                calls.attach_mock(self.flush, "flush")
                calls.attach_mock(self.run, "poweroff")
                response = self.client.post("/shutdown", environ_overrides={"REMOTE_ADDR": address})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.get_json(), {"success": True})
                self.assertEqual([call[0] for call in calls.mock_calls], ["flush", "poweroff"])
                self.run.assert_called_with(["sudo", "-n", "/usr/bin/systemctl", "poweroff"],
                                            check=True, timeout=5, capture_output=True)
        self.timer.assert_not_called()
        self.kill.assert_not_called()

    def test_shutdown_persistence_exception_aborts_poweroff(self):
        self.flush.side_effect = OSError("database unavailable")
        response = self.client.post("/shutdown")
        self.assertEqual(response.status_code, 500)
        self.assertIn("shutdown aborted", response.get_json()["error"])
        self.run.assert_not_called()

    def test_poweroff_errors_are_json_and_never_report_acceptance(self):
        failures = [
            subprocess.CalledProcessError(1, "sudo"),
            subprocess.TimeoutExpired("sudo", 5),
            FileNotFoundError("sudo"),
            PermissionError("systemctl"),
        ]
        for error in failures:
            with self.subTest(error=error):
                self.run.side_effect = error
                response = self.client.post("/shutdown")
                self.assertEqual(response.status_code, 500)
                self.assertIn("error", response.get_json())
                self.assertNotIn("success", response.get_json())

    def test_exit_rejects_boardless_even_when_enabled(self):
        with patch.dict(os.environ, {"BOARDLESS_MODE": "TRUE"}):
            response = self.client.post("/kiosk/exit")
        self.assertEqual(response.status_code, 403)
        self.assertIn("boardless", response.get_json()["error"])
        self.flush.assert_not_called()
        self.timer.assert_not_called()
        self.kill.assert_not_called()

    def test_exit_disabled_rejects_before_flush(self):
        with patch.dict(os.environ, {"KIOSK_SHUTDOWN_ENABLED": "false"}):
            response = self.client.post("/kiosk/exit")
        self.assertEqual(response.status_code, 403)
        self.flush.assert_not_called()
        self.timer.assert_not_called()

    def test_exit_preserves_flush_then_runner_termination(self):
        calls = Mock()
        calls.attach_mock(self.flush, "flush")
        calls.attach_mock(self.timer, "timer")
        response = self.client.post("/kiosk/exit")
        self.assertEqual(response.get_json(), {"success": True})
        self.assertEqual([call[0] for call in calls.mock_calls], ["flush", "timer", "timer().start"])
        self.timer.assert_called_once_with(0.1, api_main.terminate_kiosk_runner)
        self.run.assert_not_called()
        with patch("api.main.os.getppid", return_value=123):
            self.timer.call_args.args[1]()
        self.kill.assert_called_once_with(123, signal.SIGTERM)

    def test_exit_persistence_and_scheduling_errors_are_json(self):
        self.flush.side_effect = RuntimeError("cannot save")
        response = self.client.post("/kiosk/exit")
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.get_json())
        self.timer.assert_not_called()
        self.flush.side_effect = None
        self.timer.return_value.start.side_effect = RuntimeError("cannot schedule")
        response = self.client.post("/kiosk/exit")
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.get_json())

    def test_unsuccessful_database_update_aborts_both_actions_without_losing_usage(self):
        # Use the real flush wrapper/tracker; only the database write is simulated.
        tracker = StylusHoursTracker(lambda: {"id": "1", "hours": 100}, Mock(return_value=False))
        tracker.process_play("00:00")
        tracker.process_play("04:00")
        self.flush.side_effect = self.real_flush
        with patch("api.main.stylus_hours_tracker", tracker):
            for endpoint in ("/shutdown", "/kiosk/exit"):
                response = self.client.post(endpoint)
                self.assertEqual(response.status_code, 500)
                self.assertIn("error", response.get_json())
                self.assertEqual(tracker.pending_seconds, 240)
        self.run.assert_not_called()
        self.timer.assert_not_called()

    def test_successful_shutdown_persists_actual_pending_hours(self):
        increment = Mock(return_value=True)
        tracker = StylusHoursTracker(lambda: {"id": "1", "hours": 100}, increment)
        tracker.process_play("00:00")
        tracker.process_play("04:00")
        self.flush.side_effect = self.real_flush
        self.run.side_effect = lambda *args, **kwargs: self.assertEqual(tracker.pending_seconds, 0)
        with patch("api.main.stylus_hours_tracker", tracker):
            response = self.client.post("/shutdown")
        self.assertEqual(response.get_json(), {"success": True})
        increment.assert_called_once_with("1", 240 / 3600)


if __name__ == "__main__":
    unittest.main()

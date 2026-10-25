import io
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import ExitStack, redirect_stdout
from types import SimpleNamespace
from unittest.mock import Mock, patch

import api.main as api_main
from api.nfc_coordinator import NfcCoordinator, NfcShuttingDown
from api.stylus_hours import StylusHoursTracker
import lib.nfc as nfc_module
from exp.nfc import nfc_debug_i2c


class NfcShutdownTestCase(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.close = Mock()
        self.coordinator = NfcCoordinator(close_nfc=self.close, logger=api_main.app.logger)
        replacements = {
            "nfc_coordinator": self.coordinator,
            "nfc_coordinator_started": False,
            "nfc_coordinator_thread": None,
            "nfc_coordinator_lock": threading.RLock(),
            "shutdown_started": threading.Event(),
            "shutdown_cleanup_lock": threading.Lock(),
            "shutdown_result": False,
            "shutdown_signal_in_progress": False,
            "shutdown_hooks_installed": False,
            "previous_signal_handlers": {},
        }
        for name, value in replacements.items():
            self.stack.enter_context(patch.object(api_main, name, value))
        self.flush = self.stack.enter_context(patch.object(api_main, "flush_pending_stylus_usage"))
        self.stack.enter_context(patch.dict(os.environ, {"BOARDLESS_MODE": "false"}))

    def test_normal_server_return_uses_same_cleanup_and_saves_stylus_usage(self):
        increment = Mock(return_value=True)
        tracker = StylusHoursTracker(lambda: {"id": "1", "hours": 100}, increment)
        tracker.process_play("00:00")
        tracker.process_play("04:00")
        self.flush.side_effect = lambda: tracker.flush_pending()
        result = api_main.start_api_server(
            install_hooks=lambda: None, verify_sensors=lambda: None,
            start_temperature=lambda: None, start_playback=lambda: None,
            run_flask=lambda: "server returned",
        )
        self.assertEqual(result, "server returned")
        self.assertFalse(api_main.nfc_coordinator_thread.is_alive())
        self.assertTrue(api_main.shutdown_application())
        self.close.assert_called_once_with()
        self.flush.assert_called_once_with()
        increment.assert_called_once_with("1", 240 / 3600)

    def test_startup_failure_closes_initialized_backend_in_worker(self):
        backend = Mock()
        close_threads = []
        backend.close.side_effect = lambda: close_threads.append(threading.current_thread())
        self.coordinator.close_nfc = nfc_module.close_backend
        with patch.object(nfc_module, "_backend", backend), patch.object(nfc_module, "_get_backend") as initialize:
            with self.assertRaisesRegex(api_main.SensorReadinessError, "RPM sensor readiness check failed"):
                api_main.start_api_server(
                    install_hooks=lambda: None,
                    verify_sensors=lambda: api_main.verify_required_sensors_ready(
                        boardless_mode=lambda: False, verify_nfc=lambda: None,
                        verify_rpm=Mock(side_effect=OSError("rpm failed")),
                    ),
                )
            self.assertTrue(api_main.shutdown_application())
            initialize.assert_not_called()
        backend.close.assert_called_once_with()
        self.assertEqual(close_threads, [api_main.nfc_coordinator_thread])

    def test_failed_thread_start_still_allows_startup_cleanup(self):
        real_thread = threading.Thread
        attempts = []
        def thread_factory(*args, **kwargs):
            attempts.append(kwargs["name"])
            if len(attempts) == 1:
                return Mock(start=Mock(side_effect=RuntimeError("cannot start worker")))
            return real_thread(*args, **kwargs)
        with patch("api.main.threading.Thread", side_effect=thread_factory):
            with self.assertRaisesRegex(RuntimeError, "cannot start worker"):
                api_main.start_api_server(
                    install_hooks=lambda: None, verify_sensors=lambda: None,
                    start_temperature=lambda: None, start_playback=lambda: None,
                )
        self.assertEqual(attempts, ["nfc-worker", "nfc-cleanup"])
        self.close.assert_called_once_with()

    def test_boardless_shutdown_does_not_initialize_or_prompt(self):
        self.coordinator.close_nfc = nfc_module.close_backend
        with patch.dict(os.environ, {"BOARDLESS_MODE": "true"}), patch.object(nfc_module, "_backend", None):
            with patch.object(nfc_module, "_get_backend") as initialize, patch("builtins.input") as prompt:
                self.assertFalse(api_main.start_nfc_coordinator())
                self.assertTrue(api_main.shutdown_application())
                self.assertTrue(api_main.shutdown_application())
        initialize.assert_not_called()
        prompt.assert_not_called()

    def test_five_second_limit_includes_active_read_and_does_not_start_second_command(self):
        reading, release = threading.Event(), threading.Event()
        commands = []
        def read(timeout):
            commands.append("read")
            reading.set()
            release.wait(10)
            return "1"
        self.coordinator.read_nfc = read
        self.coordinator.write_nfc = lambda record_id: commands.append("write")
        self.coordinator.set_mode("standby")
        api_main.start_nfc_coordinator()
        try:
            self.assertTrue(reading.wait(2))
            self.coordinator.request_write("queued")
            started = time.monotonic()
            with self.assertLogs(api_main.app.logger, level="INFO") as logs:
                self.assertFalse(api_main.shutdown_application())
                elapsed = time.monotonic() - started
                self.assertFalse(api_main.shutdown_application())
            self.assertGreaterEqual(elapsed, 4.9)
            self.assertLess(elapsed, 6)
            self.assertEqual(api_main.NFC_SHUTDOWN_TIMEOUT_SECONDS, 5)
            self.assertTrue(api_main.nfc_coordinator_thread.is_alive())
            self.assertEqual(commands, ["read"])
            self.close.assert_not_called()
            self.assertIn("NFC shutdown incomplete after 5s", "\n".join(logs.output))
            self.assertFalse(api_main.start_nfc_coordinator())
        finally:
            release.set()
            api_main.nfc_coordinator_thread.join(2)
        self.assertFalse(api_main.nfc_coordinator_thread.is_alive())
        self.close.assert_called_once_with()
        self.assertEqual(commands, ["read"])

    def test_wait_includes_reader_close_and_repeated_signal_does_not_interrupt_it(self):
        closing, release = threading.Event(), threading.Event()
        def close():
            closing.set()
            release.wait(2)
        self.close.side_effect = close
        worker = threading.Thread(target=api_main.shutdown_application)
        worker.start()
        try:
            self.assertTrue(closing.wait(2))
            self.assertTrue(worker.is_alive())
            self.assertFalse(api_main.shutdown_application())
            api_main.shutdown_signal_handler(signal.SIGTERM, None)
            self.assertTrue(worker.is_alive())
        finally:
            release.set()
            worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertTrue(api_main.shutdown_application())
        self.close.assert_called_once_with()

    def test_blocked_close_has_same_limit_without_second_close(self):
        closing, release = threading.Event(), threading.Event()
        self.close.side_effect = lambda: (closing.set(), release.wait(2))
        with patch.object(api_main, "NFC_SHUTDOWN_TIMEOUT_SECONDS", 0.05):
            try:
                with self.assertLogs(api_main.app.logger, level="ERROR") as logs:
                    self.assertFalse(api_main.shutdown_application())
                self.assertTrue(closing.is_set())
                self.assertTrue(api_main.nfc_coordinator_thread.is_alive())
                self.assertFalse(api_main.shutdown_application())
                self.assertIn("worker remains active", "\n".join(logs.output))
                self.close.assert_called_once_with()
            finally:
                release.set()
                api_main.nfc_coordinator_thread.join(2)

    def test_cleanup_failure_still_flushes_usage_and_logs_failure(self):
        self.close.side_effect = nfc_module.NfcError("RF-off failed")
        with self.assertLogs(api_main.app.logger, level="INFO") as logs:
            self.assertFalse(api_main.shutdown_application())
        self.assertIn("NFC reader cleanup failed", "\n".join(logs.output))
        self.assertIn("cleanup_succeeded=False", "\n".join(logs.output))
        self.flush.assert_called_once_with()

    def test_stylus_save_failure_does_not_skip_reader_cleanup(self):
        self.flush.side_effect = OSError("database failed")
        with self.assertLogs(api_main.app.logger, level="ERROR"):
            self.assertFalse(api_main.shutdown_application())
        self.close.assert_called_once_with()

    def test_signal_and_exit_hooks_use_common_cleanup(self):
        with patch("api.main.atexit.register") as register, patch("api.main.signal.signal"):
            api_main.install_shutdown_hooks()
        register.assert_called_once_with(api_main.shutdown_application)
        api_main.previous_signal_handlers = {signal.SIGTERM: signal.SIG_DFL}
        with self.assertRaises(SystemExit) as raised:
            api_main.shutdown_signal_handler(signal.SIGTERM, None)
        self.assertEqual(raised.exception.code, 0)
        api_main.shutdown_signal_handler(signal.SIGTERM, None)
        api_main.shutdown_signal_handler(signal.SIGINT, None)
        register.call_args.args[0]()
        self.close.assert_called_once_with()
        self.flush.assert_called_once_with()

    def test_nfc_endpoints_reject_shutdown_and_racing_requests_as_json_503(self):
        client = api_main.app.test_client()
        endpoints = [("/nfc/mode", {"mode": "standby"}, "set_mode"),
                     ("/nfc/write", {"record_id": "1"}, "request_write")]
        for endpoint, payload, method in endpoints:
            with self.subTest(endpoint=endpoint):
                with patch.object(self.coordinator, method, side_effect=NfcShuttingDown("NFC is shutting down")):
                    response = client.post(endpoint, json=payload)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.get_json(), {"error": "NFC is shutting down"})
        self.coordinator.stop()
        for endpoint, payload, _ in endpoints:
            response = client.post(endpoint, json=payload)
            self.assertEqual(response.status_code, 503)
            self.assertTrue(response.is_json)


class I2cDiagnosticTestCase(unittest.TestCase):
    def test_diagnostic_reports_actual_bus_error_and_closes_transport(self):
        for number, description in ((5, "Input/output error"), (110, "Connection timed out"), (121, "Remote I/O error")):
            with self.subTest(errno=number):
                bus = Mock()
                bus.i2c_rdwr.side_effect = OSError(number, description)
                smbus = SimpleNamespace(SMBus=Mock(return_value=bus), i2c_msg=Mock())
                output = io.StringIO()
                with patch.dict(sys.modules, {"smbus2": smbus}), redirect_stdout(output):
                    nfc_debug_i2c.main()
                self.assertIn(description, output.getvalue())
                self.assertIn(f"errno={number}", output.getvalue())
                self.assertNotIn("No ACK", output.getvalue())
                bus.close.assert_called_once_with()


class NfcShutdownSubprocessTestCase(unittest.TestCase):
    def run_process(self, tag="present", scenario="signal"):
        root = Path(__file__).resolve().parents[1]
        helper = root / "tests" / "fixtures" / "nfc_shutdown_process.py"
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "shutdown.log"
            process = subprocess.Popen(
                [sys.executable, str(helper), str(log), tag, scenario], cwd=root,
                env={**os.environ, "PYTHONPATH": str(root), "BOARDLESS_MODE": "false"},
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            try:
                if scenario != "atexit":
                    deadline = time.monotonic() + 5
                    while time.monotonic() < deadline:
                        if log.exists() and "read-start" in log.read_text():
                            break
                        if process.poll() is not None:
                            self.fail(f"Process exited before read: {process.communicate()}")
                        time.sleep(0.01)
                    else:
                        self.fail("Subprocess did not start a Standby read")
                    process.send_signal(signal.SIGTERM)
                started = time.monotonic()
                stdout, stderr = process.communicate(timeout=7)
                self.assertEqual(process.returncode, 0, stdout + stderr)
                return log.read_text().splitlines(), stderr, time.monotonic() - started
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()

    def test_termination_during_standby_read_finishes_cleanup_before_normal_exit(self):
        for tag in ("present", "absent"):
            with self.subTest(tag=tag):
                events, stderr, _ = self.run_process(tag)
                self.assertEqual(events, ["read-start", "read-end", "rf-off", "rf-off", "transport-close",
                                          "stylus-flush", "process-exit"])
                self.assertIn("NFC reader cleanup succeeded", stderr)
                self.assertNotIn("shutdown incomplete", stderr)

    def test_registered_process_exit_cleanup_waits_for_worker(self):
        events, stderr, _ = self.run_process(scenario="atexit")
        self.assertEqual(events, ["read-start", "read-end", "rf-off", "rf-off", "transport-close",
                                  "stylus-flush", "process-exit"])
        self.assertIn("NFC reader cleanup succeeded", stderr)

    def test_blocked_worker_does_not_prevent_process_exit_after_five_seconds(self):
        events, stderr, elapsed = self.run_process(scenario="blocked")
        self.assertGreaterEqual(elapsed, 4.9)
        self.assertLess(elapsed, 6)
        self.assertEqual(events, ["read-start", "stylus-flush", "process-exit"])
        self.assertIn("NFC shutdown incomplete after 5s", stderr)


if __name__ == "__main__":
    unittest.main()

import unittest
import threading
import logging
from unittest.mock import Mock

from api.nfc_coordinator import NfcCoordinator, NfcShuttingDown
from lib.nfc import NfcError, NfcNoCard


class NfcCoordinatorTestCase(unittest.TestCase):
    def make_coordinator(self, **overrides):
        messages = []
        defaults = {
            "read_nfc": lambda timeout: "1",
            "write_nfc": lambda record_id: None,
            "broadcast": messages.append,
            "persist_link_success": lambda record_id: True,
            "close_nfc": lambda: None,
        }
        defaults.update(overrides)
        return NfcCoordinator(**defaults), messages

    def test_standby_polling_runs_only_in_standby(self):
        read_calls = []
        coordinator, _ = self.make_coordinator(read_nfc=lambda timeout: read_calls.append(timeout) or "1")

        for mode in ("sync", "link", "re-link", "stylus", "play"):
            coordinator.set_mode(mode)
            coordinator.tick()

        self.assertEqual(read_calls, [])

        coordinator.set_mode("standby")
        coordinator.tick()

        self.assertEqual(read_calls, [0.2])

    def test_scan_event_suppression_continues_through_errors_after_success(self):
        reads = iter([
            NfcNoCard("none"),
            "1",
            "1",
            NfcNoCard("none"),
            "2",
            NfcError("bad read"),
            NfcError("still bad"),
            NfcNoCard("none"),
            NfcError("bad again"),
        ])

        def read_nfc(timeout):
            result = next(reads)
            if isinstance(result, Exception):
                raise result
            return result

        coordinator, messages = self.make_coordinator(read_nfc=read_nfc)
        coordinator.set_mode("standby")

        for _ in range(9):
            coordinator.tick()

        self.assertEqual(
            messages,
            [
                {"event": "scan", "data": {"record_id": "1"}},
                {"event": "scan", "data": {"record_id": "2"}},
            ],
        )
        self.assertEqual(coordinator.last_successful_record_id, "2")
        self.assertEqual(coordinator.last_emitted_record_id, "2")
        self.assertFalse(coordinator.scan_error_emitted)

    def test_startup_error_is_emitted_once_until_first_successful_read(self):
        reads = iter([
            NfcError("bad read"),
            NfcNoCard("none"),
            NfcError("still bad"),
            "1",
            NfcError("bad again"),
            "1",
        ])

        def read_nfc(timeout):
            result = next(reads)
            if isinstance(result, Exception):
                raise result
            return result

        coordinator, messages = self.make_coordinator(read_nfc=read_nfc)
        coordinator.set_mode("standby")

        for _ in range(6):
            coordinator.tick()

        self.assertEqual(
            messages,
            [
                {"event": "scan", "data": {"record_id": None}},
                {"event": "scan", "data": {"record_id": "1"}},
            ],
        )
        self.assertEqual(coordinator.last_successful_record_id, "1")
        self.assertEqual(coordinator.last_emitted_record_id, "1")
        self.assertFalse(coordinator.scan_error_emitted)

    def test_same_record_remains_suppressed_after_read_error_and_no_card(self):
        reads = iter([
            "1",
            NfcError("bad read"),
            NfcNoCard("none"),
            "1",
            "1",
        ])

        def read_nfc(timeout):
            result = next(reads)
            if isinstance(result, Exception):
                raise result
            return result

        coordinator, messages = self.make_coordinator(read_nfc=read_nfc)
        coordinator.set_mode("standby")

        for _ in range(5):
            coordinator.tick()

        self.assertEqual(
            messages,
            [
                {"event": "scan", "data": {"record_id": "1"}},
            ],
        )
        self.assertEqual(coordinator.last_successful_record_id, "1")
        self.assertEqual(coordinator.last_emitted_record_id, "1")
        self.assertFalse(coordinator.scan_error_emitted)

    def test_unlinked_scanned_record_emits_real_id_once(self):
        coordinator, messages = self.make_coordinator(
            read_nfc=lambda timeout: "1",
        )
        coordinator.set_mode("standby")

        coordinator.tick()
        coordinator.tick()

        self.assertEqual(messages, [{"event": "scan", "data": {"record_id": "1"}}])
        self.assertEqual(coordinator.last_successful_record_id, "1")
        self.assertEqual(coordinator.last_emitted_record_id, "1")
        self.assertFalse(coordinator.scan_error_emitted)

    def test_active_write_request_pauses_standby_polling_and_writes_exact_record_id(self):
        calls = []

        def read_nfc(timeout):
            calls.append(("read", timeout))
            return "2"

        def write_nfc(record_id):
            calls.append(("write", record_id))

        coordinator, messages = self.make_coordinator(read_nfc=read_nfc, write_nfc=write_nfc)
        coordinator.set_mode("standby")
        coordinator.request_write("abc-123", mode="link")

        coordinator.tick()

        self.assertEqual(calls, [("write", "abc-123")])
        self.assertEqual(messages, [{"event": "link_success", "data": {"record_id": "abc-123"}}])

    def test_link_success_persists_before_broadcast(self):
        order = []

        coordinator, messages = self.make_coordinator(
            persist_link_success=lambda record_id: order.append(("persist", record_id)) or True,
            broadcast=lambda message: order.append(("broadcast", message)) or messages.append(message),
        )

        coordinator.request_write("1", mode="re-link")
        coordinator.tick()

        self.assertEqual(order[0], ("persist", "1"))
        self.assertEqual(order[1], ("broadcast", {"event": "link_success", "data": {"record_id": "1"}}))

    def test_link_error_broadcasts_on_write_failure_or_persist_failure(self):
        coordinator, write_messages = self.make_coordinator(
            write_nfc=lambda record_id: (_ for _ in ()).throw(NfcError("write failed")),
        )
        coordinator.request_write("1", mode="link")
        coordinator.tick()

        persist_coordinator, persist_messages = self.make_coordinator(
            persist_link_success=lambda record_id: False,
        )
        persist_coordinator.request_write("2", mode="re-link")
        persist_coordinator.tick()

        self.assertEqual(write_messages, [{"event": "link_error", "data": {"record_id": "1"}}])
        self.assertEqual(persist_messages, [{"event": "link_error", "data": {"record_id": "2"}}])

    def test_mode_change_and_write_request_do_not_compete_with_inflight_read(self):
        reading = threading.Event()
        finish_read = threading.Event()
        writing = threading.Event()
        calls, failures = [], []

        def read_nfc(timeout):
            calls.append(("read_started", timeout))
            reading.set()
            if not finish_read.wait(2):
                raise AssertionError("Read was not released")
            calls.append(("read_cleanup", None))
            return "1"

        def write_nfc(record_id):
            writing.set()
            calls.append(("write", record_id))

        coordinator, _ = self.make_coordinator(read_nfc=read_nfc, write_nfc=write_nfc)
        coordinator.set_mode("standby")
        def tick():
            try:
                coordinator.tick()
            except BaseException as error:
                failures.append(error)

        first, second = threading.Thread(target=tick), threading.Thread(target=tick)
        first.start()
        try:
            self.assertTrue(reading.wait(2))
            coordinator.set_mode("re-link")
            coordinator.request_write("abc-123", mode="re-link")
            self.assertEqual(calls, [("read_started", 0.2)])
            second.start()
            self.assertFalse(writing.wait(0.02))
        finally:
            finish_read.set()
            first.join(2)
            if second.ident is not None:
                second.join(2)
        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertEqual(failures, [])
        self.assertEqual(calls, [("read_started", 0.2), ("read_cleanup", None), ("write", "abc-123")])
        coordinator.tick()
        self.assertEqual(len(calls), 3)

    def test_stop_interrupts_idle_pause_and_closes_in_worker(self):
        paused = threading.Event()
        closed_by = []
        coordinator, _ = self.make_coordinator(
            close_nfc=lambda: closed_by.append(threading.current_thread()),
            poll_interval_seconds=60,
        )
        original_tick = coordinator.tick
        def tick():
            original_tick()
            paused.set()
        coordinator.tick = tick
        worker = threading.Thread(target=coordinator.run_forever)
        worker.start()
        try:
            self.assertTrue(paused.wait(2))
        finally:
            coordinator.stop()
            worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(closed_by, [worker])
        self.assertTrue(coordinator.cleanup_succeeded)

    def test_stop_during_read_discards_queue_and_cannot_restart_work(self):
        reading, release = threading.Event(), threading.Event()
        calls = []
        def read(timeout):
            calls.append("read")
            reading.set()
            if not release.wait(2):
                raise AssertionError("Read was not released")
            calls.append("read_finished")
            raise NfcError("read failed")
        coordinator, messages = self.make_coordinator(
            read_nfc=read,
            write_nfc=lambda record_id: calls.append("write"),
            close_nfc=lambda: calls.append("close"),
        )
        coordinator.last_successful_record_id = "43"
        coordinator.set_mode("standby")
        worker = threading.Thread(target=coordinator.run_forever)
        worker.start()
        try:
            self.assertTrue(reading.wait(2))
            coordinator.request_write("15")
            coordinator.stop()
            coordinator.stop()
            for operation in (lambda: coordinator.set_mode("standby"), lambda: coordinator.request_write("23")):
                with self.assertRaises(NfcShuttingDown):
                    operation()
        finally:
            release.set()
            worker.join(2)
        coordinator.tick()
        self.assertFalse(worker.is_alive())
        self.assertEqual(calls, ["read", "read_finished", "close"])
        self.assertIsNone(coordinator.active_write_request)
        self.assertEqual(coordinator.last_successful_record_id, "43")
        self.assertEqual(messages, [])

    def test_active_write_finishes_persistence_and_event_before_close(self):
        writing, release = threading.Event(), threading.Event()
        calls = []
        def write(record_id):
            calls.append(("write", record_id))
            writing.set()
            if not release.wait(2):
                raise AssertionError("Write was not released")
        coordinator, _ = self.make_coordinator(
            write_nfc=write,
            persist_link_success=lambda record_id: calls.append(("persist", record_id)) or True,
            broadcast=lambda message: calls.append(("event", message)),
            close_nfc=lambda: calls.append(("close", None)),
        )
        coordinator.request_write("abc-123", mode="re-link")
        worker = threading.Thread(target=coordinator.run_forever)
        worker.start()
        try:
            self.assertTrue(writing.wait(2))
            coordinator.request_write("queued")
            coordinator.stop()
        finally:
            release.set()
            worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(calls, [
            ("write", "abc-123"), ("persist", "abc-123"),
            ("event", {"event": "link_success", "data": {"record_id": "abc-123"}}), ("close", None),
        ])

    def test_worker_finally_closes_after_unexpected_error_and_reports_close_failure(self):
        close = Mock(side_effect=NfcError("RF-off failed"))
        coordinator, _ = self.make_coordinator(close_nfc=close, logger=logging.getLogger("nfc-finally-test"))
        coordinator.tick = Mock(side_effect=RuntimeError("worker failed"))
        with self.assertLogs("nfc-finally-test", level="INFO") as logs:
            with self.assertRaisesRegex(RuntimeError, "worker failed"):
                coordinator.run_forever()
        close.assert_called_once_with()
        self.assertFalse(coordinator.cleanup_succeeded)
        self.assertTrue(coordinator.shutting_down)
        self.assertIn("NFC reader cleanup failed", "\n".join(logs.output))

    def test_error_log_keeps_transport_stage_errno_and_original_exception(self):
        bus_error = OSError(121, "Remote I/O error")
        def read(timeout):
            try:
                raise bus_error
            except OSError as error:
                raise NfcError(f"I2C ACK read failed: {error}") from error
        coordinator, _ = self.make_coordinator(read_nfc=read, logger=logging.getLogger("nfc-error-test"))
        coordinator.set_mode("standby")
        with self.assertLogs("nfc-error-test", level="ERROR") as logs:
            coordinator.tick()
        output = "\n".join(logs.output)
        self.assertIn("OSError: [Errno 121] Remote I/O error", output)
        self.assertIn("I2C ACK read failed", output)


if __name__ == "__main__":
    unittest.main()

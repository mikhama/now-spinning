import unittest

from api.nfc_coordinator import NfcCoordinator
from lib.nfc import NfcError, NfcNoCard


class NfcCoordinatorTestCase(unittest.TestCase):
    def make_coordinator(self, **overrides):
        messages = []
        defaults = {
            "read_nfc": lambda timeout: "1",
            "write_nfc": lambda record_id: None,
            "broadcast": messages.append,
            "persist_link_success": lambda record_id: True,
            "sleep": lambda seconds: None,
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

        self.assertEqual(read_calls, [1])

    def test_scan_event_suppression_and_error_payloads(self):
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
                {"event": "scan", "data": {"record_id": None}},
                {"event": "scan", "data": {"record_id": None}},
            ],
        )
        self.assertEqual(coordinator.last_successful_record_id, "2")
        self.assertEqual(coordinator.last_emitted_record_id, "2")

    def test_unlinked_scanned_record_emits_nfc_error_scan_without_activating_record(self):
        coordinator, messages = self.make_coordinator(
            read_nfc=lambda timeout: "1",
            is_record_linked=lambda record_id: False,
        )
        coordinator.set_mode("standby")

        coordinator.tick()

        self.assertEqual(messages, [{"event": "scan", "data": {"record_id": None}}])
        self.assertIsNone(coordinator.last_successful_record_id)
        self.assertIsNone(coordinator.last_emitted_record_id)

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


if __name__ == "__main__":
    unittest.main()

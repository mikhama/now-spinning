import unittest

import lib.nfc as nfc_module
from lib.nfc import BoardlessBackend, NfcError, NfcNoCard, Pn532Backend, nfc_read, nfc_read_once, nfc_write
from unittest.mock import patch
from unittest.mock import Mock

from drv.pn532 import PN532Commands


class FakeBackend:
    def __init__(self):
        self.read_calls = []
        self.writes = []
        self.read_result = "1"
        self.read_error = None
        self.write_error = None

    def read(self, timeout=30):
        self.read_calls.append(timeout)
        if self.read_error:
            raise self.read_error
        return self.read_result

    def write(self, text):
        self.writes.append(text)
        if self.write_error:
            raise self.write_error


NO_CARD_OVERRIDE = object()


class FakePn532:
    def __init__(self, card_type="ntag_ultralight", card=NO_CARD_OVERRIDE):
        self.card_type = card_type
        self.card = {"uid": b"\x01\x02\x03\x04"} if card is NO_CARD_OVERRIDE else card
        self.wait_timeouts = []
        self.classic_blocks = {}
        self.ntag_pages = {}
        self.classic_writes = []
        self.ntag_writes = []
        self.fail_read = False
        self.fail_write = False
        self.auth_ok = True
        self.rf_enabled = False
        self.rf_calls = []
        self.actions = []

    def action(self, name, address):
        if not self.rf_enabled:
            raise AssertionError("Payload operation while RF is off")
        self.actions.append((name, address))

    def set_rf_field(self, enabled):
        self.rf_calls.append(enabled)
        self.rf_enabled = enabled
        return True

    def wait_for_card(self, timeout=30):
        self.wait_timeouts.append(timeout)
        self.set_rf_field(True)
        return self.card

    def identify_card(self, card):
        return self.card_type

    def classic_auth(self, block, uid):
        self.action("auth", block)
        return self.auth_ok

    def classic_read(self, block):
        self.action("classic_read", block)
        if self.fail_read:
            return None
        return self.classic_blocks.get(block)

    def classic_write(self, block, chunk):
        self.action("classic_write", block)
        if self.fail_write:
            return False
        self.classic_writes.append((block, bytes(chunk)))
        return True

    def classic_is_trailer(self, block):
        return (block + 1) % 4 == 0

    def ntag_read(self, page):
        self.action("ntag_read", page)
        if self.fail_read:
            return None
        return self.ntag_pages.get(page)

    def ntag_write(self, page, chunk):
        self.action("ntag_write", page)
        if self.fail_write:
            return False
        self.ntag_writes.append((page, bytes(chunk)))
        return True


def make_backend(fake_nfc):
    backend = Pn532Backend.__new__(Pn532Backend)
    backend._nfc = fake_nfc
    return backend


class NfcLibraryTestCase(unittest.TestCase):
    def setUp(self):
        self.original_backend = nfc_module._backend

    def tearDown(self):
        nfc_module._backend = self.original_backend

    def test_nfc_read_compatibility_uses_default_backend_timeout(self):
        fake = FakeBackend()
        nfc_module._backend = fake

        self.assertEqual(nfc_read(), "1")
        self.assertEqual(fake.read_calls, [30])

    def test_short_timeout_read_distinguishes_no_card(self):
        fake = FakeBackend()
        fake.read_error = NfcNoCard("No card detected")
        nfc_module._backend = fake

        with self.assertRaises(NfcNoCard):
            nfc_read_once(timeout=1)

        self.assertEqual(fake.read_calls, [1])

    def test_short_timeout_read_surfaces_read_errors(self):
        fake = FakeBackend()
        fake.read_error = NfcError("Read failed")
        nfc_module._backend = fake

        with self.assertRaises(NfcError):
            nfc_read_once(timeout=0.5)

        self.assertNotIsInstance(fake.read_error, NfcNoCard)

    def test_pn532_no_card_raises_specific_no_card_error(self):
        fake_nfc = FakePn532(card=None)
        backend = make_backend(fake_nfc)

        with self.assertRaises(NfcNoCard):
            backend.read(timeout=1)

        self.assertEqual(fake_nfc.wait_timeouts, [1])

    def test_pn532_successful_ntag_read_returns_text_payload(self):
        fake_nfc = FakePn532(card_type="ntag_ultralight")
        fake_nfc.ntag_pages[4] = bytes([3]) + b"abc" + bytes(12)
        backend = make_backend(fake_nfc)

        self.assertEqual(backend.read(timeout=1), "abc")

    def test_pn532_read_failure_raises_nfc_error(self):
        fake_nfc = FakePn532(card_type="mifare_classic_1k")
        fake_nfc.auth_ok = False
        backend = make_backend(fake_nfc)

        with self.assertRaisesRegex(NfcError, "Read failed"):
            backend.read(timeout=1)

    def test_nfc_write_surfaces_write_errors(self):
        fake = FakeBackend()
        fake.write_error = NfcError("Write failed")
        nfc_module._backend = fake

        with self.assertRaises(NfcError):
            nfc_write("1")

        self.assertEqual(fake.writes, ["1"])

    def test_pn532_ntag_write_stores_exact_text_payload(self):
        fake_nfc = FakePn532(card_type="ntag_ultralight")
        backend = make_backend(fake_nfc)

        backend.write("abc-123")

        payload = b"".join(chunk for _, chunk in fake_nfc.ntag_writes)
        self.assertEqual(payload[:8], bytes([7]) + b"abc-123")

    def test_pn532_classic_write_stores_exact_text_payload(self):
        fake_nfc = FakePn532(card_type="mifare_classic_1k")
        backend = make_backend(fake_nfc)

        backend.write("1")

        self.assertEqual(fake_nfc.classic_writes, [(4, bytes([1]) + b"1" + bytes(14))])

    def test_multi_page_and_block_reads_keep_rf_through_complete_payload(self):
        text = "a" * 60
        payload = (bytes([len(text)]) + text.encode()).ljust(64, b"\x00")
        for card_type in ("ntag_ultralight", "mifare_classic_1k"):
            with self.subTest(card_type=card_type):
                fake = FakePn532(card_type=card_type)
                if "classic" in card_type:
                    fake.classic_blocks = dict(zip((4, 5, 6, 8), [payload[i:i+16] for i in range(0, 64, 16)]))
                else:
                    fake.ntag_pages = {4 + i // 4: payload[i:i+16] for i in range(0, 64, 16)}
                self.assertEqual(make_backend(fake).read(), text)
                self.assertEqual(fake.rf_calls, [True, False])
                self.assertFalse(fake.rf_enabled)
                if "classic" in card_type:
                    self.assertEqual(fake.actions[-2:], [("auth", 8), ("classic_read", 8)])
                else:
                    self.assertEqual(fake.actions[-1], ("ntag_read", 16))

    def test_multi_page_and_block_writes_keep_rf_through_complete_payload(self):
        for card_type in ("ntag_ultralight", "mifare_classic_1k"):
            with self.subTest(card_type=card_type):
                fake = FakePn532(card_type=card_type)
                make_backend(fake).write("a" * 60)
                self.assertEqual(fake.rf_calls, [True, False])
                self.assertFalse(fake.rf_enabled)
                writes = fake.classic_writes if "classic" in card_type else fake.ntag_writes
                self.assertEqual(b"".join(data for _, data in writes)[:61], b"\x3c" + b"a" * 60)

    def test_rf_cleanup_on_timeout_auth_failure_transfer_failure_and_interruption(self):
        for operation in ("read", "write"):
            for failure in ("no_card", "auth", "transfer", "interrupt", "transport"):
                with self.subTest(operation=operation, failure=failure):
                    fake = FakePn532(card_type="mifare_classic_1k")
                    fake.classic_blocks[4] = b"\x01a" + bytes(14)
                    if failure == "no_card":
                        fake.card = None
                    elif failure == "auth":
                        fake.auth_ok = False
                    else:
                        method = "classic_read" if operation == "read" else "classic_write"
                        error = {"transfer": NfcError("transfer"), "interrupt": KeyboardInterrupt(),
                                 "transport": OSError("bus failed")}[failure]
                        self.enterContext(patch.object(fake, method, side_effect=error))
                    expected = KeyboardInterrupt if failure == "interrupt" else NfcError
                    with self.assertRaises(expected):
                        if operation == "read":
                            make_backend(fake).read()
                        else:
                            make_backend(fake).write("abc")
                    self.assertFalse(fake.rf_enabled)
                    self.assertEqual(fake.rf_calls[-1], False)

    def test_cleanup_failure_surfaces_and_keeps_original_context(self):
        for operation_error in (None, NfcNoCard("none"), OSError("bus failed"), KeyboardInterrupt()):
            with self.subTest(operation_error=operation_error):
                fake = FakePn532()
                fake.ntag_pages[4] = b"\x01a" + bytes(14)
                original_set_rf = fake.set_rf_field
                def set_rf(enabled):
                    if not enabled:
                        raise OSError("off broken")
                    return original_set_rf(enabled)
                self.enterContext(patch.object(fake, "set_rf_field", side_effect=set_rf))
                if operation_error:
                    self.enterContext(patch.object(fake, "ntag_read", side_effect=operation_error))
                with self.assertRaisesRegex(NfcError, "RF-off failed") as raised:
                    make_backend(fake).read()
                error, contexts = raised.exception, []
                while error is not None:
                    contexts.append(error)
                    error = error.__context__
                if operation_error:
                    self.assertIn(operation_error, contexts)

    def test_malformed_payload_and_later_classic_auth_failure_are_errors(self):
        fake = FakePn532()
        fake.ntag_pages[4] = b"\x01\xff" + bytes(14)
        with self.assertRaises(NfcError):
            make_backend(fake).read()
        self.assertFalse(fake.rf_enabled)
        classic = FakePn532(card_type="mifare_classic_1k")
        classic.classic_blocks[4] = b"\x20" + b"a" * 15
        with patch.object(classic, "classic_auth", side_effect=[True, False]):
            with self.assertRaisesRegex(NfcError, "Read failed"):
                make_backend(classic).read()
        self.assertFalse(classic.rf_enabled)

    def test_false_rf_off_result_is_an_error(self):
        fake = FakePn532(card=None)
        with patch.object(fake, "set_rf_field", return_value=False):
            with self.assertRaisesRegex(NfcError, "RF-off failed"):
                make_backend(fake).read()

    def test_boardless_read_and_write_remain_interactive(self):
        with patch("builtins.input", side_effect=[" abc-123 ", "y"]), patch("builtins.print") as output:
            backend = BoardlessBackend()
            self.assertEqual(backend.read(), "abc-123")
            backend.write("abc-123")
            output.assert_called_once_with('[BOARDLESS] Write: "abc-123"')

    def test_cleanup_never_initializes_a_backend(self):
        nfc_module._backend = None
        with patch.object(nfc_module, "_get_backend") as initialize:
            nfc_module.close_backend()
            nfc_module.close_backend()
        initialize.assert_not_called()

    def test_close_is_safe_to_repeat_after_success_or_rf_failure(self):
        for failure in (None, OSError(5, "I2C command write failed")):
            with self.subTest(failure=failure):
                driver = PN532Commands()
                driver.set_rf_field = Mock(return_value=True, side_effect=failure)
                driver._close_connection = Mock()
                backend = make_backend(driver)
                nfc_module._backend = backend
                if failure:
                    with self.assertRaisesRegex(NfcError, "RF-off failed") as raised:
                        nfc_module.close_backend()
                    self.assertIs(raised.exception.__cause__, failure)
                else:
                    nfc_module.close_backend()
                nfc_module.close_backend()
                backend.close()
                driver.set_rf_field.assert_called_once_with(False)
                driver._close_connection.assert_called_once_with()
                self.assertIsNone(nfc_module._backend)

    def test_boardless_close_does_not_prompt_or_initialize_hardware(self):
        with patch("builtins.input") as prompt, patch.object(nfc_module, "Pn532Backend") as hardware:
            with patch.dict("os.environ", {"BOARDLESS_MODE": "true"}):
                nfc_module._backend = None
                self.assertIsInstance(nfc_module.initialize_backend(), BoardlessBackend)
                nfc_module.close_backend()
                nfc_module.close_backend()
        prompt.assert_not_called()
        hardware.assert_not_called()


if __name__ == "__main__":
    unittest.main()

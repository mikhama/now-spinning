import unittest

import lib.nfc as nfc_module
from lib.nfc import NfcError, NfcNoCard, Pn532Backend, nfc_read, nfc_read_once, nfc_write


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

    def wait_for_card(self, timeout=30):
        self.wait_timeouts.append(timeout)
        return self.card

    def identify_card(self, card):
        return self.card_type

    def classic_auth(self, block, uid):
        return self.auth_ok

    def classic_read(self, block):
        if self.fail_read:
            return None
        return self.classic_blocks.get(block)

    def classic_write(self, block, chunk):
        if self.fail_write:
            return False
        self.classic_writes.append((block, bytes(chunk)))
        return True

    def classic_is_trailer(self, block):
        return (block + 1) % 4 == 0

    def ntag_read(self, page):
        if self.fail_read:
            return None
        return self.ntag_pages.get(page)

    def ntag_write(self, page, chunk):
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


if __name__ == "__main__":
    unittest.main()

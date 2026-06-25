"""NFC library: hardware-backed or boardless simulation backend."""

import os

PN532_MODE = 1  # 0 = UART, 1 = I2C
START_BLOCK = 4


class NfcError(Exception):
    """Raised on NFC read/write failure."""


# ── PN532 hardware backend ────────────────────────────────────────────────────

class Pn532Backend:

    def __init__(self):
        if PN532_MODE == 0:
            from drv.pn532_uart import PN532
            conn = "/dev/ttyUSB0"   # serial port
        else:
            from drv.pn532_i2c import PN532
            conn = 6                # I2C bus number
        self._nfc = PN532(conn)

    def read(self) -> str:
        card = self._nfc.wait_for_card(timeout=30)
        if not card:
            raise NfcError("No card detected")
        card_type = self._nfc.identify_card(card)
        if "classic" in card_type:
            text = self._read_classic(card["uid"])
        else:
            text = self._read_ntag()
        if text is None:
            raise NfcError("Read failed")
        return text

    def _read_classic(self, uid) -> str | None:
        if not self._nfc.classic_auth(START_BLOCK, uid):
            return None
        data = self._nfc.classic_read(START_BLOCK)
        if not data:
            return None
        text_len = data[0]
        if text_len == 0 or text_len == 0xFF:
            return None
        raw = bytearray(data)
        block = START_BLOCK + 1
        while len(raw) < text_len + 1:
            while self._nfc.classic_is_trailer(block):
                block += 1
            if not self._nfc.classic_auth(block, uid):
                break
            data = self._nfc.classic_read(block)
            if not data:
                break
            raw.extend(data)
            block += 1
        return raw[1 : 1 + text_len].decode("utf-8", errors="replace")

    def _read_ntag(self) -> str | None:
        data = self._nfc.ntag_read(START_BLOCK)
        if not data:
            return None
        text_len = data[0]
        if text_len == 0 or text_len == 0xFF:
            return None
        raw = bytearray(data)
        page = START_BLOCK + 4
        while len(raw) < text_len + 1:
            data = self._nfc.ntag_read(page)
            if not data:
                break
            raw.extend(data)
            page += 4
        return raw[1 : 1 + text_len].decode("utf-8", errors="replace")

    def write(self, text: str) -> None:
        card = self._nfc.wait_for_card(timeout=30)
        if not card:
            raise NfcError("No card detected")
        card_type = self._nfc.identify_card(card)
        if "classic" in card_type:
            ok = self._write_classic(card["uid"], text)
        else:
            ok = self._write_ntag(text)
        if not ok:
            raise NfcError("Write failed")

    def _write_classic(self, uid, text: str) -> bool:
        encoded = text.encode("utf-8")
        payload = bytearray([len(encoded)]) + bytearray(encoded)
        while len(payload) % 16 != 0:
            payload.append(0x00)
        block = START_BLOCK
        for i in range(0, len(payload), 16):
            while self._nfc.classic_is_trailer(block):
                block += 1
            chunk = payload[i : i + 16]
            if not self._nfc.classic_auth(block, uid):
                return False
            if not self._nfc.classic_write(block, chunk):
                return False
            block += 1
        return True

    def _write_ntag(self, text: str) -> bool:
        encoded = text.encode("utf-8")
        payload = bytearray([len(encoded)]) + bytearray(encoded)
        while len(payload) % 4 != 0:
            payload.append(0x00)
        page = START_BLOCK
        for i in range(0, len(payload), 4):
            chunk = payload[i : i + 4]
            if not self._nfc.ntag_write(page, chunk):
                return False
            page += 1
        return True


# ── Boardless simulation backend ──────────────────────────────────────────────

class BoardlessBackend:

    def read(self) -> str:
        text = input("[BOARDLESS] Enter simulated card text (empty to cancel): ").strip()
        if not text:
            raise NfcError("No input provided (read cancelled)")
        return text

    def write(self, text: str) -> None:
        print(f'[BOARDLESS] Write: "{text}"')
        confirm = input("Confirm write? [y/N]: ").strip().lower()
        if confirm != "y":
            raise NfcError("Write not confirmed (cancelled)")


# ── Module-level lazy backend and public API ──────────────────────────────────

_backend = None


def _get_backend():
    global _backend
    if _backend is None:
        if os.environ.get("BOARDLESS_MODE", "").lower() == "true":
            _backend = BoardlessBackend()
        else:
            _backend = Pn532Backend()
    return _backend


def nfc_read() -> str:
    return _get_backend().read()


def nfc_write(text: str) -> None:
    _get_backend().write(text)

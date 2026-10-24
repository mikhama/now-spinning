"""Shared PN532 protocol and card operations for I2C and UART."""

import time

from lib.nfc_errors import NfcError


class PN532Commands:
    HOST_TO_PN = 0xD4
    PN_TO_HOST = 0xD5

    CMD_FIRMWARE_VERSION  = 0x02
    CMD_SAM_CONFIGURATION = 0x14
    CMD_RF_CONFIGURATION  = 0x32
    CMD_IN_LIST_PASSIVE   = 0x4A
    CMD_IN_DATA_EXCHANGE  = 0x40

    MIFARE_AUTH_A       = 0x60
    MIFARE_AUTH_B       = 0x61
    MIFARE_READ         = 0x30
    MIFARE_WRITE_16     = 0xA0
    MIFARE_WRITE_4      = 0xA2

    DEFAULT_KEY = b'\xFF\xFF\xFF\xFF\xFF\xFF'

    DETECTION_TIMEOUT = 0.2
    RF_OFF_PAUSE = 1.0
    _ACK = b'\x00\x00\xff\x00\xff\x00'

    def _initialize(self):
        try:
            try:
                self._wakeup()
                self.set_passive_retries(0x00)
                self.disable_rf_field()
            except NfcError:
                raise
            except Exception as error:
                raise NfcError(f"PN532 initialization failed: {error}") from error
        except BaseException as initialization_error:
            try:
                self.close()
            except Exception as cleanup_error:
                raise NfcError(
                    f"PN532 initialization failed: {initialization_error}; "
                    f"cleanup also failed: {cleanup_error}"
                ) from initialization_error
            raise

    def _build_frame(self, data):
        length = len(data)
        return (bytes([0, 0, 0xff, length, (-length) & 0xff])
                + bytes(data) + bytes([(-sum(data)) & 0xff, 0]))

    def _pop_frame(self, buffer):
        """Consume one complete, checked frame; retain partial UART packets."""
        pos = buffer.find(b'\x00\x00\xff')
        if pos < 0:
            if any(buffer):
                raise NfcError("Malformed PN532 frame header")
            del buffer[:-2]
            return None
        if any(buffer[:pos]):
            raise NfcError("Malformed PN532 frame prefix")
        del buffer[:pos]
        if len(buffer) < 6:
            return None
        if buffer[:6] == self._ACK:
            del buffer[:6]
            return ('ack', b'')
        length, checksum = buffer[3:5]
        if length < 2 or (length + checksum) & 0xff:
            raise NfcError("Malformed PN532 frame length")
        size = length + 7
        if len(buffer) < size:
            return None
        data = bytes(buffer[5:5 + length])
        if (sum(data) + buffer[5 + length]) & 0xff or buffer[6 + length] != 0:
            raise NfcError("Malformed PN532 frame checksum/postamble")
        if data[0] != self.PN_TO_HOST:
            raise NfcError("Malformed PN532 response direction")
        del buffer[:size]
        return ('response', data)

    def send_command(self, cmd, params=b'', timeout=2):
        """Wait for ACK and the expected response under one monotonic deadline."""
        if cmd == self.CMD_IN_LIST_PASSIVE:
            timeout = min(timeout, self.DETECTION_TIMEOUT)
        deadline = time.monotonic() + max(0, timeout)
        buffer = bytearray()
        acknowledged = False
        try:
            self._prepare_command()
            if time.monotonic() >= deadline:
                raise NfcError(f"PN532 command {cmd:#04x} timed out")
            self._write_frame(self._build_frame(bytes([self.HOST_TO_PN, cmd]) + params), deadline)
            while time.monotonic() < deadline:
                buffer.extend(self._read_chunk(deadline, acknowledged=acknowledged))
                if time.monotonic() > deadline:
                    break
                while (frame := self._pop_frame(buffer)) is not None:
                    kind, data = frame
                    if kind == 'ack':
                        acknowledged = True
                    elif acknowledged and data[1] == (cmd + 1) & 0xff:
                        return data[2:]
                    # Unrelated responses (including replies before ACK) are stale.
            raise NfcError(f"PN532 command {cmd:#04x} timed out waiting for expected response")
        except OSError as error:
            raise NfcError(f"PN532 transport failed for command {cmd:#04x}: {error}") from error

    def set_passive_retries(self, max_retries=0x00):
        response = self.send_command(
            self.CMD_RF_CONFIGURATION, bytes([0x05, 0xff, 0x01, max_retries]))
        if response != b'':
            raise NfcError("Passive activation retry configuration failed")
        return True

    def set_rf_field(self, enabled: bool) -> bool:
        response = self.send_command(self.CMD_RF_CONFIGURATION, bytes([0x01, int(enabled)]))
        if response != b'':
            raise NfcError(f"RF-{'on' if enabled else 'off'} command failed")
        return True

    def disable_rf_field(self):
        try:
            if not self.set_rf_field(False):
                raise NfcError("RF-off command was not confirmed")
        except Exception as error:
            raise NfcError(f"RF-off failed: {error}") from error

    def get_firmware_version(self):
        response = self.send_command(self.CMD_FIRMWARE_VERSION)
        if len(response) != 4:
            raise NfcError("Malformed firmware version response")
        return dict(zip(('ic', 'ver', 'rev', 'support'), response))

    def read_passive_target(self, timeout=2):
        """Probe once; a found card retains RF until backend payload cleanup."""
        deadline = time.monotonic() + max(0, min(timeout, self.DETECTION_TIMEOUT))
        found = False
        try:
            if not self.set_rf_field(True):
                raise NfcError("RF-on command was not confirmed")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise NfcError("Detection deadline expired while enabling RF")
            response = self.send_command(self.CMD_IN_LIST_PASSIVE, b'\x01\x00', remaining)
            if response == b'\x00':
                return None
            if (len(response) < 6 or response[0] != 1 or response[1] != 1
                    or response[5] not in (4, 7, 10) or len(response) < 6 + response[5]):
                raise NfcError("Malformed passive target response")
            card = {'uid': response[6:6 + response[5]],
                    'atqa': response[2:4], 'sak': response[4]}
            found = True
            return card
        finally:
            if not found:
                self.disable_rf_field()

    def wait_for_card(self, timeout=30):
        deadline = time.monotonic() + max(0, timeout)
        while (remaining := deadline - time.monotonic()) > 0:
            card = self.read_passive_target(timeout=min(self.DETECTION_TIMEOUT, remaining))
            if card is not None:
                return card
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(min(self.RF_OFF_PAUSE, remaining))
        return None

    def identify_card(self, card):
        sak = card['sak']
        types = {
            0x00: 'ntag_ultralight',
            0x08: 'mifare_classic_1k',
            0x09: 'mifare_mini',
            0x18: 'mifare_classic_4k',
            0x20: 'iso14443_4',
        }
        return types.get(sak, f'unknown_sak_{sak:#04x}')

    # ── Mifare Classic ────────────────────────────────────

    def classic_auth(self, block, uid, key=None, key_type=None):
        if key is None:
            key = self.DEFAULT_KEY
        if key_type is None:
            key_type = self.MIFARE_AUTH_A
        params = bytearray([0x01, key_type, block])
        params.extend(key)
        params.extend(uid[:4])
        resp = self.send_command(self.CMD_IN_DATA_EXCHANGE, params)
        return resp is not None and len(resp) >= 1 and resp[0] == 0x00

    def classic_read(self, block):
        """Read 16 bytes from a Mifare Classic block."""
        params = bytearray([0x01, self.MIFARE_READ, block])
        resp = self.send_command(self.CMD_IN_DATA_EXCHANGE, params)
        if resp and len(resp) >= 17 and resp[0] == 0x00:
            return bytes(resp[1:17])
        return None

    def classic_write(self, block, data):
        """Write 16 bytes to a Mifare Classic block."""
        assert len(data) == 16, "Classic block = 16 bytes"
        params = bytearray([0x01, self.MIFARE_WRITE_16, block])
        params.extend(data)
        resp = self.send_command(self.CMD_IN_DATA_EXCHANGE, params)
        return resp is not None and len(resp) >= 1 and resp[0] == 0x00

    @staticmethod
    def classic_is_trailer(block):
        return (block + 1) % 4 == 0

    # ── NTAG / Ultralight ─────────────────────────────────

    def ntag_read(self, page):
        """Read 16 bytes (4 pages) starting at page."""
        params = bytearray([0x01, self.MIFARE_READ, page])
        resp = self.send_command(self.CMD_IN_DATA_EXCHANGE, params)
        if resp and len(resp) == 17 and resp[0] == 0x00:
            return bytes(resp[1:17])
        return None

    def ntag_write(self, page, data):
        """Write 4 bytes to a single page."""
        assert len(data) == 4, "NTAG page = 4 bytes"
        params = bytearray([0x01, self.MIFARE_WRITE_4, page])
        params.extend(data)
        resp = self.send_command(self.CMD_IN_DATA_EXCHANGE, params)
        return resp is not None and len(resp) >= 1 and resp[0] == 0x00

    def close(self):
        try:
            self.disable_rf_field()
        finally:
            try:
                self._close_connection()
            except OSError as error:
                raise NfcError(f"PN532 connection close failed: {error}") from error

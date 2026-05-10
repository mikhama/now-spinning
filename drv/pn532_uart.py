"""
PN532 driver over USB serial (HSU mode).
Only needs: pip install pyserial
"""

import serial
import time


class PN532:
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

    def __init__(self, port="/dev/ttyUSB0", baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=0.5)
        time.sleep(0.1)
        self._wakeup()

    def _wakeup(self):
        """nfcpy-style wakeup: 0x55 preamble + zeros + SAMConfig in one write."""
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

        wakeup = (
            b'\x55\x55'
            b'\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00'
        )
        sam_frame = self._build_frame(
            bytearray([self.HOST_TO_PN, self.CMD_SAM_CONFIGURATION, 0x01])
        )
        self.ser.write(wakeup + sam_frame)
        time.sleep(0.3)
        self.ser.read(self.ser.in_waiting or 100)

        # Configure retries for passive target detection
        self.set_passive_retries(0xFF)

    # ── Frame building / parsing ──────────────────────────

    def _build_frame(self, data):
        """Build a PN532 HSU frame."""
        length = len(data)
        lcs = (~length + 1) & 0xFF
        dcs = (~sum(data) + 1) & 0xFF
        frame = bytearray([0x00, 0x00, 0xFF, length, lcs])
        frame.extend(data)
        frame.append(dcs)
        frame.append(0x00)
        return bytes(frame)

    def _read_raw(self, timeout=1):
        """Read all available bytes within timeout."""
        deadline = time.time() + timeout
        buf = bytearray()
        while time.time() < deadline:
            avail = self.ser.in_waiting
            if avail:
                buf.extend(self.ser.read(avail))
                time.sleep(0.02)
            else:
                if buf:
                    time.sleep(0.05)
                    avail = self.ser.in_waiting
                    if avail:
                        buf.extend(self.ser.read(avail))
                    break
                time.sleep(0.02)
        return bytes(buf)

    def _parse_response(self, raw):
        """Extract payload from response bytes (skip ACK + frame header)."""
        idx = 0
        while idx < len(raw):
            pos = raw.find(b'\x00\x00\xFF', idx)
            if pos < 0:
                return None
            if pos + 3 >= len(raw):
                return None

            length = raw[pos + 3]

            # Skip ACK frames (length = 0)
            if length == 0:
                idx = pos + 6
                continue

            # Data frame
            data_start = pos + 5
            data_end = data_start + length

            if data_end > len(raw):
                return None

            data = raw[data_start:data_end]

            if len(data) >= 2 and data[0] == self.PN_TO_HOST:
                return bytes(data[2:])

            idx = pos + 3
        return None

    def send_command(self, cmd, params=b'', timeout=2):
        """Send a command and return the response payload."""
        data = bytearray([self.HOST_TO_PN, cmd])
        data.extend(params)
        frame = self._build_frame(data)

        self.ser.reset_input_buffer()
        self.ser.write(frame)

        raw = self._read_raw(timeout)
        return self._parse_response(raw)

    # ── High-level commands ───────────────────────────────

    def get_firmware_version(self):
        resp = self.send_command(self.CMD_FIRMWARE_VERSION)
        if resp and len(resp) >= 4:
            return {
                'ic': resp[0], 'ver': resp[1],
                'rev': resp[2], 'support': resp[3],
            }
        return None

    def set_passive_retries(self, max_retries=0xFF):
        """Configure PN532 to retry card detection.
        0xFF = retry indefinitely until card found."""
        params = bytearray([0x05, 0xFF, 0x01, max_retries])
        self.send_command(self.CMD_RF_CONFIGURATION, params)

    def read_passive_target(self, timeout=2):
        """Detect a card. Returns dict with uid, atqa, sak or None."""
        resp = self.send_command(
            self.CMD_IN_LIST_PASSIVE,
            bytearray([0x01, 0x00]),
            timeout,
        )
        if resp and len(resp) >= 7 and resp[0] >= 1:
            # resp[0]   = NbTg (number of targets)
            # resp[1]   = Tg   (target number)
            # resp[2:4] = SENS_RES (ATQA, 2 bytes)
            # resp[4]   = SEL_RES (SAK)
            # resp[5]   = NFCIDLength
            # resp[6:]  = NFCID1 (UID)
            uid_len = resp[5]
            return {
                'uid':  bytes(resp[6:6 + uid_len]),
                'atqa': bytes(resp[2:4]),
                'sak':  resp[4],
            }
        return None

    def wait_for_card(self, timeout=30):
        """Keep scanning until a card is found or timeout."""
        print("Place card on reader...", flush=True)
        deadline = time.time() + timeout
        while time.time() < deadline:
            card = self.read_passive_target(timeout=2)
            if card:
                uid_hex = card['uid'].hex(':')
                card_type = self.identify_card(card)
                print(f"\n  UID:  {uid_hex}")
                print(f"  ATQA: {card['atqa'].hex(':')}")
                print(f"  SAK:  {card['sak']:#04x}")
                print(f"  Type: {card_type}\n")
                return card
            time.sleep(0.1)
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
        if resp and len(resp) >= 5 and resp[0] == 0x00:
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
        self.ser.close()
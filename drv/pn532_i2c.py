"""
PN532 driver over I2C (e.g. Raspberry Pi).

Wiring (this project): PN532 on I2C bus 6
    SDA -> GPIO22 (pin 15)
    SCL -> GPIO23 (pin 16)
    VCC -> 3.3V   (shared off pin 17)
    GND -> any GND pin (25/30/34/39)

Enable the bus first:  add `dtoverlay=i2c6` to /boot/firmware/config.txt, reboot.
Confirm:               i2cdetect -y 6   ->  device at 0x24

Dependencies:  pip install smbus2
The PN532 I2C address is fixed at 0x24.

This class is a drop-in replacement for the UART PN532: it exposes the same
public methods, so the rest of the codebase does not change (other than which
driver it imports and the "port" it is given, which is now a bus number).
"""

import time

try:
    from smbus2 import SMBus, i2c_msg
except ImportError as e:
    raise ImportError(
        "smbus2 is required for the I2C driver. Install with: pip install smbus2"
    ) from e


class PN532:
    HOST_TO_PN = 0xD4
    PN_TO_HOST = 0xD5

    I2C_ADDRESS = 0x24

    CMD_FIRMWARE_VERSION  = 0x02
    CMD_SAM_CONFIGURATION = 0x14
    CMD_RF_CONFIGURATION  = 0x32
    CMD_IN_LIST_PASSIVE   = 0x4A
    CMD_IN_DATA_EXCHANGE  = 0x40

    MIFARE_AUTH_A   = 0x60
    MIFARE_AUTH_B   = 0x61
    MIFARE_READ     = 0x30
    MIFARE_WRITE_16 = 0xA0
    MIFARE_WRITE_4  = 0xA2

    DEFAULT_KEY = b'\xFF\xFF\xFF\xFF\xFF\xFF'

    # PN532 ACK frame
    _ACK = b'\x00\x00\xFF\x00\xFF\x00'

    def __init__(self, bus=6, address=I2C_ADDRESS):
        """
        `bus` is the I2C bus number (6 for this project's i2c6 wiring).
        For backwards compatibility, a string like "/dev/ttyUSB0" is tolerated
        and mapped to bus 6 with a warning, so callers that still pass the old
        PORT value don't crash.
        """
        if isinstance(bus, str):
            # Old code may still pass a serial device path; fall back sensibly.
            print(f"[WARN] PN532(I2C) got a string '{bus}'; using I2C bus 6 instead.")
            bus = 6
        self.address = address
        self.bus = SMBus(bus)
        time.sleep(0.1)
        self._wakeup()

    # ── Low-level I2C transport ───────────────────────────

    def _i2c_write(self, frame):
        msg = i2c_msg.write(self.address, frame)
        self.bus.i2c_rdwr(msg)

    def _i2c_read(self, count):
        """Read `count` bytes. The PN532 prepends a status byte (0x01=ready)."""
        msg = i2c_msg.read(self.address, count + 1)
        self.bus.i2c_rdwr(msg)
        data = bytes(msg)
        if not data:
            return b''
        # First byte is the I2C status/ready byte; strip it.
        return data[1:]

    def _wait_ready(self, timeout=1.0):
        """Poll until the PN532 signals it is ready (status byte 0x01)."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                msg = i2c_msg.read(self.address, 1)
                self.bus.i2c_rdwr(msg)
                status = bytes(msg)
                if status and status[0] == 0x01:
                    return True
            except OSError:
                pass
            time.sleep(0.01)
        return False

    def _read_ack(self, timeout=1.0):
        if not self._wait_ready(timeout):
            return False
        data = self._i2c_read(len(self._ACK))
        return data[:len(self._ACK)] == self._ACK

    # ── Frame building / parsing ──────────────────────────

    def _build_frame(self, data):
        """Build a standard PN532 information frame."""
        length = len(data)
        lcs = (~length + 1) & 0xFF
        dcs = (~sum(data) + 1) & 0xFF
        frame = bytearray([0x00, 0x00, 0xFF, length, lcs])
        frame.extend(data)
        frame.append(dcs)
        frame.append(0x00)
        return bytes(frame)

    def _parse_response(self, raw):
        """Extract the PN532->host payload from a response buffer."""
        if not raw:
            return None
        pos = raw.find(b'\x00\x00\xFF')
        if pos < 0 or pos + 4 >= len(raw):
            return None

        length = raw[pos + 3]
        if length == 0:
            return None  # ACK / empty

        data_start = pos + 5
        data_end = data_start + length
        if data_end > len(raw):
            return None

        data = raw[data_start:data_end]
        if len(data) >= 2 and data[0] == self.PN_TO_HOST:
            return bytes(data[2:])
        return None

    def _wakeup(self):
        """SAMConfiguration normal mode + configure detection retries."""
        # On I2C there is no 0x55 preamble needed; just send SAMConfig.
        self.send_command(
            self.CMD_SAM_CONFIGURATION,
            bytearray([0x01, 0x14, 0x01]),  # normal mode, timeout, use IRQ pin
        )
        self.set_passive_retries(0xFF)

    def send_command(self, cmd, params=b'', timeout=2):
        """Send a command frame, read the ACK, then read the response payload."""
        data = bytearray([self.HOST_TO_PN, cmd])
        data.extend(params)
        frame = self._build_frame(data)

        try:
            self._i2c_write(frame)
        except OSError:
            return None

        # PN532 must ACK the command first.
        if not self._read_ack(timeout):
            return None

        # Then wait for the response to be ready and read it.
        if not self._wait_ready(timeout):
            return None

        # Read a generous buffer; short responses are zero-padded/ignored.
        raw = self._i2c_read(64)
        return self._parse_response(raw)

    # ── High-level commands (identical interface to UART driver) ──

    def get_firmware_version(self):
        resp = self.send_command(self.CMD_FIRMWARE_VERSION)
        if resp and len(resp) >= 4:
            return {
                'ic': resp[0], 'ver': resp[1],
                'rev': resp[2], 'support': resp[3],
            }
        return None

    def set_passive_retries(self, max_retries=0xFF):
        params = bytearray([0x05, 0xFF, 0x01, max_retries])
        self.send_command(self.CMD_RF_CONFIGURATION, params)

    def read_passive_target(self, timeout=2):
        resp = self.send_command(
            self.CMD_IN_LIST_PASSIVE,
            bytearray([0x01, 0x00]),
            timeout,
        )
        if resp and len(resp) >= 7 and resp[0] >= 1:
            uid_len = resp[5]
            return {
                'uid':  bytes(resp[6:6 + uid_len]),
                'atqa': bytes(resp[2:4]),
                'sak':  resp[4],
            }
        return None

    def wait_for_card(self, timeout=30):
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
        params = bytearray([0x01, self.MIFARE_READ, block])
        resp = self.send_command(self.CMD_IN_DATA_EXCHANGE, params)
        if resp and len(resp) >= 17 and resp[0] == 0x00:
            return bytes(resp[1:17])
        return None

    def classic_write(self, block, data):
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
        params = bytearray([0x01, self.MIFARE_READ, page])
        resp = self.send_command(self.CMD_IN_DATA_EXCHANGE, params)
        if resp and len(resp) >= 5 and resp[0] == 0x00:
            return bytes(resp[1:17])
        return None

    def ntag_write(self, page, data):
        assert len(data) == 4, "NTAG page = 4 bytes"
        params = bytearray([0x01, self.MIFARE_WRITE_4, page])
        params.extend(data)
        resp = self.send_command(self.CMD_IN_DATA_EXCHANGE, params)
        return resp is not None and len(resp) >= 1 and resp[0] == 0x00

    def close(self):
        self.bus.close()
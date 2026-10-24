"""PN532 driver over USB serial (HSU mode); requires pyserial."""

import serial
import time

from drv.pn532 import PN532Commands
from lib.nfc_errors import NfcError


class PN532(PN532Commands):
    def __init__(self, port="/dev/ttyUSB0", baudrate=115200):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=0, write_timeout=2)
        except OSError as error:
            raise NfcError(f"Cannot open PN532 UART: {error}") from error
        self._initialize()

    def _wakeup(self):
        time.sleep(0.1)
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.ser.write(b'\x55\x55' + bytes(14))
        time.sleep(0.1)
        response = self.send_command(self.CMD_SAM_CONFIGURATION, b'\x01')
        if response != b'':
            raise NfcError("SAM configuration failed")

    def _prepare_command(self):
        self.ser.reset_input_buffer()

    def _write_frame(self, frame, deadline):
        self.ser.write_timeout = max(0, deadline - time.monotonic())
        if self.ser.write(frame) != len(frame):
            raise NfcError("Incomplete PN532 UART command write")

    def _read_chunk(self, deadline, *, acknowledged=False):
        while (remaining := deadline - time.monotonic()) > 0:
            available = self.ser.in_waiting
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return b''
            if available:
                return self.ser.read(available)
            time.sleep(min(0.005, remaining))
        return b''

    def _close_connection(self):
        self.ser.close()

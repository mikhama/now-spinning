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

from smbus2 import SMBus, i2c_msg

from drv.pn532 import PN532Commands
from lib.nfc_errors import NfcError


class PN532(PN532Commands):
    I2C_ADDRESS = 0x24

    def __init__(self, bus=6, address=I2C_ADDRESS):
        if isinstance(bus, str):
            print(f"[WARN] PN532(I2C) got a string '{bus}'; using I2C bus 6 instead.")
            bus = 6
        self.address = address
        try:
            self.bus = SMBus(bus)
        except OSError as error:
            raise NfcError(f"Cannot open PN532 I2C bus: {error}") from error
        self._initialize()

    def _wakeup(self):
        time.sleep(0.1)
        response = self.send_command(self.CMD_SAM_CONFIGURATION, b'\x01\x14\x01')
        if response != b'':
            raise NfcError("SAM configuration failed")

    def _prepare_command(self):
        pass

    def _write_frame(self, frame, deadline):
        self.bus.i2c_rdwr(i2c_msg.write(self.address, frame))

    def _read_chunk(self, deadline):
        while (remaining := deadline - time.monotonic()) > 0:
            status = i2c_msg.read(self.address, 1)
            self.bus.i2c_rdwr(status)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return b''
            if bytes(status) == b'\x01':
                # Includes the ready byte; remaining bytes beyond a frame are padding.
                response = i2c_msg.read(self.address, 65)
                self.bus.i2c_rdwr(response)
                raw = bytes(response)
                if not raw or raw[0] != 1:
                    raise NfcError("Malformed I2C ready status")
                return raw[1:]
            time.sleep(min(0.005, remaining))
        return b''

    def _close_connection(self):
        self.bus.close()

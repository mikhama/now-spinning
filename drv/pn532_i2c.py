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

    def _i2c_transfer(self, message, stage):
        try:
            self.bus.i2c_rdwr(message)
        except OSError as error:
            description = f"I2C {stage} failed: {error}"
            contextual_error = OSError(error.errno, description) if error.errno is not None else OSError(description)
            raise contextual_error from error

    def _write_frame(self, frame, deadline):
        self._i2c_transfer(i2c_msg.write(self.address, frame), "command write")

    def _wait_ready(self, deadline):
        last_error = None
        while (remaining := deadline - time.monotonic()) > 0:
            try:
                status = i2c_msg.read(self.address, 1)
                self._i2c_transfer(status, "ready-status read")
            except OSError as error:
                # PN532 can temporarily NACK while busy. The previous driver
                # retried these status polls; keep that behavior within the
                # command's existing deadline, without resending the command.
                last_error = error
                ready = False
            else:
                last_error = None
                ready = bytes(status) == b'\x01'
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            if ready:
                return True
            time.sleep(min(0.01, remaining))
        if last_error is not None:
            raise last_error
        return False

    def _read_chunk(self, deadline, *, acknowledged=False):
        while self._wait_ready(deadline):
            # Read the six-byte ACK separately, as in the original I2C driver.
            count = 64 if acknowledged else len(self._ACK)
            response = i2c_msg.read(self.address, count + 1)
            self._i2c_transfer(response, "response read" if acknowledged else "ACK read")
            raw = bytes(response)
            if raw and raw[0] == 0:
                # RDY=0 is a valid busy reply; following bytes are irrelevant.
                remaining = deadline - time.monotonic()
                if remaining > 0:
                    time.sleep(min(0.01, remaining))
                continue
            if not raw or raw[0] != 1:
                raise NfcError("Malformed I2C ready status")
            if not acknowledged and raw[1:] != self._ACK:
                # A previous command's response can precede the new ACK.
                # Discard the short read instead of joining it to a new frame.
                continue
            return raw[1:]
        return b''

    def _close_connection(self):
        self.bus.close()

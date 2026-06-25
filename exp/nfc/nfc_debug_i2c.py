#!/usr/bin/env python3
"""I2C debug — verify the PN532 is reachable on the bus and responds."""

I2C_BUS = 6
PN532_ADDR = 0x24


def main():
    print(f"PN532 I2C diagnostic - bus {I2C_BUS}, address {PN532_ADDR:#04x}\n")

    # 1. Can we open the bus?
    try:
        from smbus2 import SMBus, i2c_msg
    except ImportError:
        print("[ERROR] smbus2 not installed.  ->  pip install smbus2")
        return

    try:
        bus = SMBus(I2C_BUS)
    except FileNotFoundError:
        print(f"[ERROR] /dev/i2c-{I2C_BUS} not found.")
        print("        Add 'dtoverlay=i2c6' to /boot/firmware/config.txt and reboot.")
        return
    except Exception as e:
        print(f"[ERROR] Cannot open bus {I2C_BUS}: {e}")
        return
    print(f"[1] /dev/i2c-{I2C_BUS} opened OK")

    # 2. Is something ACKing at 0x24?
    try:
        bus.i2c_rdwr(i2c_msg.read(PN532_ADDR, 1))
        print(f"[2] Device ACKed at {PN532_ADDR:#04x}  OK")
    except OSError:
        print(f"[2] No ACK at {PN532_ADDR:#04x}. Check wiring / DIP switch (I2C = 1 0).")
        print(f"    Try:  i2cdetect -y {I2C_BUS}   (expect '24')")
        bus.close()
        return
    bus.close()

    # 3. Firmware handshake via the real driver
    print("\n[3] GetFirmwareVersion via driver...")
    try:
        from drv.pn532_i2c import PN532
    except ImportError:
        from pn532_i2c import PN532  # running standalone next to the driver

    nfc = PN532(I2C_BUS)
    fw = nfc.get_firmware_version()
    if fw:
        print(f"\n  FOUND PN5{fw['ic']:02X} firmware {fw['ver']}.{fw['rev']}")
    else:
        print("\n  No firmware response.")
        print("    - Power-cycle the module after changing the DIP switch.")
        print("    - Confirm VCC = 3.3V and a common GND with the Pi.")
    nfc.close()


if __name__ == "__main__":
    main()

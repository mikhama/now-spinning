#!/usr/bin/env python3
"""Raw serial debug — see exactly what the PN532 sends back."""

import serial
import serial.tools.list_ports
import time


PORT = "/dev/ttyUSB0"
BAUD = 115200


def hex_dump(data, label=""):
    if data:
        print(f"  {label}: {data.hex(' ')} ({len(data)} bytes)")
    else:
        print(f"  {label}: [nothing]")


def try_baudrate(port, baud):
    print(f"\n{'='*50}")
    print(f"Testing {port} @ {baud} baud")
    print(f"{'='*50}")

    try:
        ser = serial.Serial(port, baud, timeout=0.5)
    except Exception as e:
        print(f"[ERROR] Cannot open port: {e}")
        return False

    ser.reset_input_buffer()
    ser.reset_output_buffer()

    # ── Test 1: Wakeup ──
    print("\n[1] Sending wakeup (0x55 × 24)...")
    ser.write(b'\x55' * 24)
    time.sleep(0.3)
    resp = ser.read(ser.in_waiting or 100)
    hex_dump(resp, "recv")

    # ── Test 2: nfcpy-style wakeup + SAMConfig ──
    print("\n[2] nfcpy-style wakeup + SAMConfig...")
    ser.reset_input_buffer()
    wakeup_sam = (
        b'\x55\x55\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\xFF\x03\xFD'
        b'\xD4\x14\x01'
        b'\x17'
        b'\x00'
    )
    hex_dump(wakeup_sam, "send")
    ser.write(wakeup_sam)
    time.sleep(0.5)
    resp = ser.read(ser.in_waiting or 100)
    hex_dump(resp, "recv")

    if not resp:
        print("  ⚠ No response to SAMConfig")
        ser.close()
        return False

    # ── Test 3: GetFirmwareVersion ──
    print("\n[3] GetFirmwareVersion...")
    ser.reset_input_buffer()
    fw_cmd = b'\x00\x00\xFF\x02\xFE\xD4\x02\x2A\x00'
    hex_dump(fw_cmd, "send")
    ser.write(fw_cmd)
    time.sleep(0.5)
    resp = ser.read(ser.in_waiting or 100)
    hex_dump(resp, "recv")

    if resp and len(resp) > 6:
        idx = resp.find(b'\xD5\x03')
        if idx >= 0 and len(resp) > idx + 5:
            ic = resp[idx + 2]
            ver = resp[idx + 3]
            rev = resp[idx + 4]
            print(f"\n  ✓ FOUND PN5{ic:02X} firmware {ver}.{rev}")
            ser.close()
            return True

    # ── Test 4: Retry without wakeup ──
    print("\n[4] Retry FW (no wakeup)...")
    ser.reset_input_buffer()
    ser.write(fw_cmd)
    time.sleep(0.5)
    resp = ser.read(ser.in_waiting or 100)
    hex_dump(resp, "recv")

    # ── Test 5: Long wakeup + FW ──
    print("\n[5] Long wakeup + FW...")
    ser.reset_input_buffer()
    ser.write(b'\x55' * 50)
    time.sleep(0.3)
    ser.read(ser.in_waiting)
    time.sleep(0.1)
    ser.write(fw_cmd)
    time.sleep(0.5)
    resp = ser.read(ser.in_waiting or 100)
    hex_dump(resp, "recv")

    ser.close()
    return False


def main():
    # List all ports
    print("Available serial ports:")
    for p in serial.tools.list_ports.comports():
        print(f"  {p.device} — {p.description} [{p.hwid}]")

    print(f"\nTesting {PORT}...")
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.5)
        print(f"  ✓ Port opened: {ser.name}")
        ser.close()
    except Exception as e:
        print(f"  ✗ Cannot open: {e}")
        return

    found = try_baudrate(PORT, BAUD)

    if not found:
        for baud in [9600, 19200, 38400, 57600, 230400, 460800]:
            found = try_baudrate(PORT, baud)
            if found:
                break

    if not found:
        print("\n" + "=" * 50)
        print("PN532 did not respond.")
        print()
        print("Checklist:")
        print("  1. DIP switches set to HSU/UART mode?")
        print("     (varies by board — check your board's docs)")
        print("  2. Is the PN532 powered? (LED on?)")
        print("  3. TX/RX wires correct? (try swapping)")
        print("  4. Your adapter: PL2303 on /dev/ttyUSB0")


if __name__ == "__main__":
    main()
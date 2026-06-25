#!/usr/bin/env python3
"""Write text to Mifare Classic or NTAG/Ultralight."""

PN532_MODE = 1  # 0 = UART, 1 = I2C

if PN532_MODE == 0:
    from drv.pn532_uart import PN532
    _CONN = "/dev/ttyUSB0"   # serial port
else:
    from drv.pn532_i2c import PN532
    _CONN = 6                # I2C bus number

START_BLOCK = 4


def write_classic(nfc, uid, text):
    encoded = text.encode('utf-8')
    payload = bytearray([len(encoded)]) + bytearray(encoded)
    while len(payload) % 16 != 0:
        payload.append(0x00)

    block = START_BLOCK
    for i in range(0, len(payload), 16):
        while nfc.classic_is_trailer(block):
            block += 1

        chunk = payload[i:i + 16]

        if not nfc.classic_auth(block, uid):
            print(f"  [ERROR] Auth failed block {block}")
            return False

        if not nfc.classic_write(block, chunk):
            print(f"  [ERROR] Write failed block {block}")
            return False

        print(f"  Block {block:2d}: {chunk.hex(' ')}")
        block += 1
    return True


def write_ntag(nfc, text):
    encoded = text.encode('utf-8')
    payload = bytearray([len(encoded)]) + bytearray(encoded)
    while len(payload) % 4 != 0:
        payload.append(0x00)

    page = START_BLOCK
    for i in range(0, len(payload), 4):
        chunk = payload[i:i + 4]
        if not nfc.ntag_write(page, chunk):
            print(f"  [ERROR] Write failed page {page}")
            return False
        print(f"  Page {page:3d}: {chunk.hex(' ')}")
        page += 1
    return True


def main():
    nfc = PN532(_CONN)
    fw = nfc.get_firmware_version()
    if not fw:
        print("[ERROR] PN532 not found.")
        return
    print(f"PN532 Firmware: {fw['ver']}.{fw['rev']}\n")

    text = input("Enter text to write: ").strip()
    if not text:
        print("[ERROR] No text.")
        return

    print(f"Text:  \"{text}\" ({len(text.encode('utf-8'))} bytes)\n")

    card = nfc.wait_for_card(timeout=30)
    if not card:
        print("[ERROR] No card.")
        return

    card_type = nfc.identify_card(card)
    print("Writing...\n")

    if 'classic' in card_type:
        ok = write_classic(nfc, card['uid'], text)
    else:
        ok = write_ntag(nfc, text)

    print(f"\n{'[DONE] Written successfully ✓' if ok else '[FAILED] ✗'}")
    nfc.close()


if __name__ == "__main__":
    main()

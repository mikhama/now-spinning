#!/usr/bin/env python3
"""Read text from Mifare Classic or NTAG/Ultralight."""

from drv.pn532_uart import PN532

PORT = "/dev/ttyUSB0"
START_BLOCK = 4


def read_classic(nfc, uid):
    if not nfc.classic_auth(START_BLOCK, uid):
        print("[ERROR] Auth failed.")
        return None

    data = nfc.classic_read(START_BLOCK)
    if not data:
        print("[ERROR] Read failed.")
        return None

    text_len = data[0]
    if text_len == 0 or text_len == 0xFF:
        return None

    raw = bytearray(data)
    block = START_BLOCK + 1

    while len(raw) < text_len + 1:
        while nfc.classic_is_trailer(block):
            block += 1
        if not nfc.classic_auth(block, uid):
            break
        data = nfc.classic_read(block)
        if not data:
            break
        raw.extend(data)
        block += 1

    return raw[1:1 + text_len].decode('utf-8', errors='replace')


def read_ntag(nfc):
    data = nfc.ntag_read(START_BLOCK)
    if not data:
        print("[ERROR] Read failed.")
        return None

    text_len = data[0]
    if text_len == 0 or text_len == 0xFF:
        return None

    raw = bytearray(data)
    page = START_BLOCK + 4

    while len(raw) < text_len + 1:
        data = nfc.ntag_read(page)
        if not data:
            break
        raw.extend(data)
        page += 4

    return raw[1:1 + text_len].decode('utf-8', errors='replace')


def main():
    nfc = PN532(PORT)
    fw = nfc.get_firmware_version()
    if not fw:
        print("[ERROR] PN532 not found.")
        return
    print(f"PN532 Firmware: {fw['ver']}.{fw['rev']}\n")

    card = nfc.wait_for_card(timeout=9999)
    if not card:
        print("[ERROR] No card.")
        return

    card_type = nfc.identify_card(card)

    if 'classic' in card_type:
        text = read_classic(nfc, card['uid'])
    else:
        text = read_ntag(nfc)

    if text:
        print(f"┌────────────────────────────────┐")
        print(f"  Text: \"{text}\"")
        print(f"  Size: {len(text.encode('utf-8'))} bytes")
        print(f"└────────────────────────────────┘")
    else:
        print("[INFO] No stored text found.")

    print("\n[DONE] ✓")
    nfc.close()


if __name__ == "__main__":
    main()

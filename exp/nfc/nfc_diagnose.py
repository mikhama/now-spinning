#!/usr/bin/env python3
"""Detect card type and dump readable memory."""

PN532_MODE = 1  # 0 = UART, 1 = I2C

if PN532_MODE == 0:
    from drv.pn532_uart import PN532
    _CONN = "/dev/ttyUSB0"   # serial port
else:
    from drv.pn532_i2c import PN532
    _CONN = 6                # I2C bus number



def dump_classic(nfc, uid):
    print("--- Mifare Classic Memory Dump ---\n")

    for sector in range(16):
        first_block = sector * 4

        auth_ok = nfc.classic_auth(first_block, uid)
        if not auth_ok:
            print(f"Sector {sector:2d} | [AUTH FAILED — non-default key?]")
            card = nfc.read_passive_target()
            if not card:
                print("[ERROR] Card lost.")
                return
            uid = card['uid']
            continue

        for b in range(4):
            block = first_block + b
            data = nfc.classic_read(block)
            if data:
                hex_str = " ".join(f"{x:02X}" for x in data)
                ascii_str = "".join(
                    chr(x) if 32 <= x < 127 else "." for x in data
                )
                label = ""
                if block == 0:
                    label = " [MANUFACTURER]"
                elif nfc.classic_is_trailer(block):
                    label = " [TRAILER]"
                print(f"Block {block:2d} | {hex_str} | {ascii_str}{label}")
            else:
                print(f"Block {block:2d} | [READ ERROR]")
        print()


def dump_ntag(nfc):
    print("--- NTAG / Ultralight Memory Dump ---\n")

    for page in range(0, 60):
        data = nfc.ntag_read(page)
        if not data:
            print(f"Page {page:3d} | -- end --")
            break

        chunk = data[0:4]
        hex_str = " ".join(f"{x:02X}" for x in chunk)
        ascii_str = "".join(
            chr(x) if 32 <= x < 127 else "." for x in chunk
        )

        label = ""
        if page == 0:
            label = " [UID]"
        elif page == 2:
            label = " [Lock bytes]"
        elif page == 3:
            label = " [CC]"
        elif page == 4:
            label = " [User data start]"

        print(f"Page {page:3d} | {hex_str} | {ascii_str}{label}")


def main():
    nfc = PN532(_CONN)
    fw = nfc.get_firmware_version()
    if not fw:
        print("[ERROR] PN532 not found.")
        return
    print(f"PN532 Firmware: {fw['ver']}.{fw['rev']}\n")

    card = nfc.wait_for_card(timeout=30)
    if not card:
        print("[ERROR] No card detected within timeout.")
        return

    card_type = nfc.identify_card(card)

    if 'classic' in card_type:
        dump_classic(nfc, card['uid'])
    elif card_type == 'ntag_ultralight':
        dump_ntag(nfc)
    else:
        print("Trying Classic auth...")
        if nfc.classic_auth(0, card['uid']):
            dump_classic(nfc, card['uid'])
        else:
            print("Trying NTAG read...")
            dump_ntag(nfc)

    nfc.close()


if __name__ == "__main__":
    main()

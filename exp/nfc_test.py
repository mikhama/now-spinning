"""Simple menu demonstrating nfc_read / nfc_write from lib.nfc."""

from lib.nfc import NfcError, nfc_read, nfc_write


def main():
    print("NFC Demo — press Ctrl+C to exit")
    while True:
        print("\n[1] Read tag  [2] Write tag  [q] Quit")
        choice = input("Choice: ").strip().lower()
        if choice == "q":
            break
        elif choice == "1":
            try:
                text = nfc_read()
                print(f'Read: "{text}"')
            except NfcError as e:
                print(f"[ERROR] {e}")
        elif choice == "2":
            text = input("Text to write: ").strip()
            if not text:
                print("[ERROR] No text entered.")
                continue
            try:
                nfc_write(text)
                print("Write succeeded.")
            except NfcError as e:
                print(f"[ERROR] {e}")
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()

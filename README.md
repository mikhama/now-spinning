# now-spinning
Hobby project with Raspberry Pi.

## Development

To run the app in boardless mode:
```bash
BOARDLESS_MODE=true python -m backend.main
```

## Utils

To read NFC tag:
```bash
python -m exp.nfc.nfc_read
```

To write NFC tag:
```bash
python -m exp.nfc.nfc_write
```

To diagnose NFC card type:
```bash
python -m exp.nfc.nfc_diagnose
```

To debug PN532 module:
```bash
python -m exp.nfc.nfc_debug
```
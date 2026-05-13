# now-spinning
Hobby project with Raspberry Pi.

## Prerequisites

To create a virtual environment:
```bash
python -m venv env
```

To activate the virtual environment:
```bash
source env/bin/activate
```

To deactivate the virtual environment:
```bash
deactivate
```

To install dependencies:
```bash
pip install -r requirements.in
```

## Usage

To run the app on Pi:
```bash
python -m api.main
```

## Development

To run the app in boardless mode:
```bash
BOARDLESS_MODE=true python -m api.main
```

To run the NFC demo in boardless mode:
```bash
BOARDLESS_MODE=true python -m exp.nfc_test
```

To debug all views:
- http://127.0.0.1:5000/#standby
- http://127.0.0.1:5000/#standby-error
- http://127.0.0.1:5000/#standby-not-found
- http://127.0.0.1:5000/#play
- http://127.0.0.1:5000/#link
- http://127.0.0.1:5000/#link-error
- http://127.0.0.1:5000/#re-link
- http://127.0.0.1:5000/#stylus
- http://127.0.0.1:5000/#stylus-error

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
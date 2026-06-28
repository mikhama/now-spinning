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

To run the app in kiosk mode on Pi:
```bash
./bin/run_kiosk.sh
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
- http://127.0.0.1:5000/#sync
- http://127.0.0.1:5000/#standby
- http://127.0.0.1:5000/#standby-error
- http://127.0.0.1:5000/#standby-not-found
- http://127.0.0.1:5000/#play
- http://127.0.0.1:5000/#link
- http://127.0.0.1:5000/#link-error
- http://127.0.0.1:5000/#re-link
- http://127.0.0.1:5000/#stylus
- http://127.0.0.1:5000/#stylus-error

To send events in boardless mode (from another terminal):
```bash
# Scan a record
curl -X POST -H "Content-Type: application/json" -d '{"event":"scan","data":{"record_id":"32"}}' localhost:5000/events

# Turntable started spinning (boardless Play-mode test)
curl -X POST -H "Content-Type: application/json" -d '{"event":"status","data":{"status":"play","time":"00:01"}}' localhost:5000/events

# Turntable stopped
curl -X POST -H "Content-Type: application/json" -d '{"event":"status","data":{"status":"stop"}}' localhost:5000/events

# Record not found
curl -X POST -H "Content-Type: application/json" -d '{"event":"scan","data":{"record_id":"999"}}' localhost:5000/events

# NFC reading error
curl -X POST -H "Content-Type: application/json" -d '{"event":"scan","data":{"record_id":null}}' localhost:5000/events

# Link success
curl -X POST -H "Content-Type: application/json" -d '{"event":"link_success","data":{"record_id":"1"}}' localhost:5000/events

# Link error
curl -X POST -H "Content-Type: application/json" -d '{"event":"link_error","data":{"record_id":"1"}}' localhost:5000/events
```

The `time` field above is for boardless Play-mode UI testing. A `status: "play"` event with `time` means the turntable is spinning; any other status means it is not spinning. This does not change real board event production.

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

To debug PN532 module (UART):
```bash
python -m exp.nfc.nfc_debug_uart
```
or (I2C)
```bash
python -m exp.nfc.nfc_debug_i2c
```

### Calibration

To check IR sensor and get RPM treshold:
```bash
python -m exp.platter_spinning
```

To calibrate platter spinning detection and tonearm delay in milliseconds, edit
`SPINNING_RPM_THRESHOLD` in `exp/spinning_detection_calibration.py`, then run on
the Raspberry Pi with the platter sensor connected:
```bash
python -m exp.spinning_detection_calibration
```

For my **Dual 721** constants are the next:
- `SPINNING_RPM_THRESHOLD = 5500`
- `TONEARM_DELAY_AUTO = AVG(9098, 9677, 9686, 10058, 9670, 10165) = 9726`
- `TONEARM_DELAY_MANUAL = AVG(1823, 589, 1347, 1258, 2590, 4140) = 1958`

## TODOs:
1. Stylus prev/next buttons - saving current selected stylus.
2. It should be impossible to scan not linked record.
3. Stylus count hours during playback.
4. Played albums log with duration.
5. Add shutdown button on the right of stylus hours.
6. Add stylus hours storing mechanism.

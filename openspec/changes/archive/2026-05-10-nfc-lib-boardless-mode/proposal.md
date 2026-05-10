## Why

The project currently has NFC read/write code in `exp/nfc/` as standalone experimental scripts tightly coupled to the PN532 hardware driver. Development and testing require a physical Raspberry Pi with the NFC sensor connected. This makes it impossible to develop application logic (e.g., in `backend/`) on a regular workstation without the hardware. A proper library abstraction and a boardless simulation mode are needed to unblock off-device development.

## What Changes

- Create a `lib/` package with an `nfc` module exposing clean `nfc_read()` and `nfc_write()` functions that can be imported from application code
- Introduce a "boardless mode" — a terminal-based simulation backend where sensor responses (card UID, read data, write confirmation) can be entered manually via stdin
- The NFC library will auto-select the real PN532 driver or the boardless simulator based on configuration or environment
- Add simple usage examples in `backend/__init__.py` (or a `backend/main.py`) demonstrating how to import and use the library functions

## Capabilities

### New Capabilities
- `nfc-library`: Reusable NFC read/write library module in `lib/nfc` that abstracts over the hardware driver and provides clean `nfc_read`/`nfc_write` functions for application code
- `boardless-mode`: Terminal-based simulation backend that accepts manual sensor input via stdin, allowing development and testing without a Raspberry Pi or NFC hardware
- `backend-examples`: Simple usage examples in `backend/main.py` demonstrating library import and usage in both real and boardless modes

### Modified Capabilities
_None — no existing specs to modify._

## Impact

- New `lib/` package added to the project root
- `backend/` gains a `main.py` with example usage code
- `drv/pn532_uart.py` is not modified but is wrapped by the new library
- No new external dependencies required (boardless mode uses only stdlib `input()`)
- Import paths for application code: `from lib.nfc import nfc_read, nfc_write`

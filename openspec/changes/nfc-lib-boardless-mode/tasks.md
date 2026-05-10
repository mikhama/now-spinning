## 1. Library Package Setup

- [x] 1.1 Create `lib/__init__.py`
- [x] 1.2 Create `lib/nfc.py` with module structure, `NfcError` exception class, and backend selection logic (`BOARDLESS_MODE` env var)

## 2. PN532 Hardware Backend

- [x] 2.1 Implement `Pn532Backend` class in `lib/nfc.py` wrapping `drv.pn532_uart.PN532` with `read()` and `write(text)` methods

## 3. Boardless Simulation Backend

- [x] 3.1 Implement `BoardlessBackend` class in `lib/nfc.py` with terminal-based `read()` (prompts for text via stdin) and `write(text)` (displays text, prompts for confirmation)

## 4. Public API Functions

- [x] 4.1 Implement `nfc_read() -> str` that lazily initializes the backend and delegates to `backend.read()`, raises `NfcError` on failure
- [x] 4.2 Implement `nfc_write(text: str) -> None` that lazily initializes the backend and delegates to `backend.write(text)`, raises `NfcError` on failure

## 5. Backend Examples

- [x] 5.1 Create `backend/main.py` with a menu loop (read / write / quit) that imports and uses `lib.nfc.nfc_read` and `lib.nfc.nfc_write`

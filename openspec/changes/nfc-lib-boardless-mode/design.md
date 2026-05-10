## Context

The project is a Raspberry Pi hobby project ("now-spinning") that reads NFC tags and monitors a turntable platter. Currently, NFC functionality lives in `exp/nfc/` as standalone scripts that directly instantiate the `PN532` hardware driver from `drv/pn532_uart.py`. The `backend/` package is empty — reserved for application logic. Development happens on a separate workstation without access to the Pi or NFC hardware.

## Goals / Non-Goals

**Goals:**
- Provide a clean library API (`lib/nfc`) that application code can import without dealing with hardware details
- Enable off-Pi development via a boardless simulation mode that accepts manual terminal input
- Keep the library simple — thin wrapper, not a framework
- Demonstrate usage with examples in `backend/main.py`

**Non-Goals:**
- Rewriting or modifying the existing `drv/pn532_uart.py` driver
- Supporting NFC hardware other than PN532
- Building a full mock/test framework — boardless mode is an interactive development aid, not automated testing
- Removing or deprecating the `exp/nfc/` experimental scripts

## Decisions

### 1. Backend abstraction via a simple interface pattern

The `lib/nfc` module will define a common interface with two implementations:
- `Pn532Backend` — wraps the real `drv.pn532_uart.PN532` driver
- `BoardlessBackend` — prompts the user via `input()` for card UID, read data, and write confirmation

**Rationale**: A simple class with `read()` and `write()` methods keeps things minimal. No ABC/protocol needed — duck typing is sufficient for a hobby project.

**Alternative considered**: A single function with `if/else` on mode — rejected because it tangles real and simulated logic together.

### 2. Mode selection via environment variable

Use `BOARDLESS_MODE=true` environment variable to select the boardless backend. Default is `false` (real hardware).

**Rationale**: Environment variables are the simplest mechanism — no config files, no CLI arg parsing needed. Easy to set in a shell session or IDE run config. A boolean `true`/`false` value is clearer than a mode string.

**Alternative considered**: CLI argument (`--boardless`) — would require argparse in library code, which doesn't belong there. Config file — overkill for a boolean toggle.

### 3. Library location: `lib/nfc/`

Create `lib/__init__.py` and `lib/nfc.py` (single module, not a sub-package).

**Rationale**: Matches the user's request. A single `lib/nfc.py` file is sufficient — the module exposes `nfc_read()` and `nfc_write()` as top-level functions. If the library grows, it can be refactored into a sub-package later.

### 4. Function signatures

```python
def nfc_read() -> str
def nfc_write(text: str) -> None
```

- `nfc_read()` waits for a card, reads text, returns it. Raises `NfcError` on failure (no card, timeout, read error)
- `nfc_write(text)` waits for a card, writes text. Raises `NfcError` on failure (no card, write error)

Internally, each creates or reuses a backend instance based on the environment.

### 5. Backend examples in `backend/main.py`

A simple script with a menu loop: read a tag, write a tag, or quit. Demonstrates importing from `lib.nfc` and works in both real and boardless modes.

## Risks / Trade-offs

- **[Boardless mode is manual]** → Acceptable for a hobby project; the goal is development aid, not automated testing
- **[Singleton backend instance]** → Module-level lazy init is simple but not thread-safe. Fine for single-threaded hobby use
- **[Import path `lib.nfc`]** → `lib` is a common name that could clash with third-party packages. Mitigated by this being a standalone project, not a published package

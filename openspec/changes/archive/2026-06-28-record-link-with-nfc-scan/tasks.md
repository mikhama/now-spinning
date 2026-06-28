## 1. NFC Library

- [x] 1.1 Add a no-card result or exception type to `lib.nfc` so short read attempts can distinguish no-card absence from read/auth/decode failures.
- [x] 1.2 Add a short-timeout NFC read API that accepts a timeout suitable for the one-second standby polling cadence and preserves existing `nfc_read()` compatibility.
- [x] 1.3 Update the PN532 read implementation using the real read flow from `exp/nfc/nfc_read.py` as reference for Classic and NTAG cards.
- [x] 1.4 Verify the write path stores only the exact provided text payload, using the real write flow from `exp/nfc/nfc_write.py` as reference for Classic and NTAG cards.

## 2. Backend NFC Coordinator

- [x] 2.1 Add a backend NFC coordinator module or service that owns NFC polling state, current UI mode, last successful record id, last emitted record id, and active write requests.
- [x] 2.2 Implement standby-only polling that checks for an NFC tag about once per second only when backend mode state is standby.
- [x] 2.3 Implement scan event suppression so successful scans broadcast only when the record id changes, no-card results broadcast nothing, and read errors broadcast `{"event":"scan","data":{"record_id":null}}`.
- [x] 2.4 Implement Link/Re-Link write request handling that starts only after an explicit selected-record request, waits for a tag, writes the exact record id string, and emits one terminal success or failure event.
- [x] 2.5 Pause standby polling while a Link/Re-Link write request is active to avoid overlapping PN532 read/write operations.
- [x] 2.6 Reuse the existing link-success persistence helper before broadcasting real NFC `link_success` events.

## 3. API and Frontend Wiring

- [x] 3.1 Add an API route or WebSocket message path for the frontend to report the active UI mode to the backend coordinator.
- [x] 3.2 Send backend mode updates from the frontend whenever the rendered mode changes, treating standby error variants as standby.
- [x] 3.3 Add an API route or WebSocket message path for Link/Re-Link button clicks to request a real NFC write for the selected record id.
- [x] 3.4 Update the frontend Link and Re-Link button handlers to keep the existing pending UI state and send the selected record id write request after the click.
- [x] 3.5 Keep real NFC broadcasts compatible with the current mock event shapes for `scan`, `link_success`, and `link_error`.
- [x] 3.6 Ensure boardless `/events` testing remains available and is not replaced by real NFC integration.

## 4. Tests and Verification

- [x] 4.1 Add unit tests for the NFC library no-card, read-error, successful-read, successful-write, and write-error behavior using fakes.
- [x] 4.2 Add backend coordinator tests proving standby polling runs only in standby and does not poll in sync, link, re-link, stylus, or play.
- [x] 4.3 Add backend coordinator tests proving scan event suppression for same record, no-card after valid scan, no-card before any valid scan, changed record id, and read error.
- [x] 4.4 Add backend/API tests proving Link/Re-Link write requests write the exact record id, persist link success before broadcast, and emit `link_error` on failure.
- [x] 4.5 Add frontend or integration tests proving mode updates and Link/Re-Link write requests are sent while existing pending/success/error UI behavior remains unchanged.
- [x] 4.6 Run the existing backend and frontend test suites, plus targeted manual verification on hardware when PN532 hardware is available.

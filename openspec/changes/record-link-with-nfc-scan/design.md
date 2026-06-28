## Context

The app already uses WebSocket events to drive standby scans and link/re-link results. Mock/testing events use these shapes: `{"event":"scan","data":{"record_id":"1"}}`, `{"event":"scan","data":{"record_id":null}}`, `{"event":"link_success","data":{"record_id":"1"}}`, and `{"event":"link_error","data":{"record_id":"1"}}`. The frontend already reacts to those shapes, and `POST /events` already validates/persists `link_success` before broadcasting it.

Real NFC support currently exists as a reusable `lib.nfc` module plus experimental scripts in `exp/nfc/nfc_read.py` and `exp/nfc/nfc_write.py`. The experimental scripts are the reference for PN532 I2C card detection, Mifare Classic reads/writes, NTAG reads/writes, and writing length-prefixed UTF-8 text starting at `START_BLOCK`.

## Goals / Non-Goals

**Goals:**

- Add real standby NFC scan polling that runs only while the app is in standby mode.
- Preserve the last successfully scanned record id when a tag leaves the reader field.
- Broadcast standby events only when the scanned record changes or a read error occurs.
- Add real Link/Re-Link write execution only after the user clicks the Link/Re-Link button.
- Broadcast Link/Re-Link outcomes using the same success/error event shapes used by mock testing.
- Write only the exact stored record id string to the NFC tag.

**Non-Goals:**

- Redesigning the frontend mode state machine or event payload contract.
- Replacing boardless `/events` testing; real NFC should coexist with it.
- Writing album metadata, release ids, or structured payloads to tags.
- Polling NFC while the UI is in play, sync, link, re-link, stylus, or any non-standby mode.

## Decisions

1. Add a backend NFC coordinator thread instead of adding polling to the frontend.

   The API server already owns WebSocket broadcasting and startup background publishers for temperature/playback. A backend coordinator can reuse those patterns, call `lib.nfc`, and emit the same events as `POST /events`. The frontend stays event-driven and does not need hardware-specific logic.

   Alternative considered: have the frontend request scans on an interval. Rejected because browser code cannot directly access the PN532, and adding polling HTTP calls would duplicate server-side event state.

2. Track UI mode on the backend using explicit mode notifications from the frontend.

   Standby scanning must run only in standby. The backend cannot infer that reliably from existing scan/status events, so the frontend should notify the server when its active mode changes. The coordinator should treat only `mode: "standby"` as scan-active; all other modes pause standby polling. Error variants such as standby not-found and standby NFC error are still standby for scan purposes.

   Alternative considered: poll continuously and let the frontend ignore scans outside standby. Rejected because the requirement is to not check every second outside standby and because continuous reads could interfere with write-ready link/re-link flows.

3. Extend `lib.nfc` with short-timeout read semantics and distinguish no-card from read failure.

   Current `nfc_read()` raises `NfcError` for both no card and failed reads after a long timeout. Standby needs a one-second cadence where no card is a non-error absence, while card read/auth/decode failures are errors. Add a library API or backend method that can attempt a read with a configurable short timeout and return a no-card result separately from raising/returning read errors. Keep the existing `nfc_read()` behavior for compatibility.

   Alternative considered: parse exception strings from existing `nfc_read()`. Rejected because string matching would make no-card behavior brittle and hard to test.

4. Broadcast scan events only on state changes that matter.

   The coordinator should keep `last_successful_record_id`, `last_emitted_record_id`, and the latest error emission state. On a successful read:
   - if the record id differs from `last_emitted_record_id`, broadcast `{"event":"scan","data":{"record_id":"<id>"}}`;
   - update the last successful id so the UI continues showing it when the tag leaves the field;
   - clear the emitted error state.

   On no-card, do not broadcast anything. If a last successful id exists, the frontend keeps showing it from the previous scan event. If no successful id exists yet, the frontend remains in its initial not-found state.

   On read error, broadcast `{"event":"scan","data":{"record_id":null}}` so the existing standby NFC error flow is used. Repeated identical errors may be suppressed until a successful read or no-card state clears the error latch.

   Alternative considered: broadcast `record_id:null` when no tag is present. Rejected because that would erase the last valid record and make tag removal look like an NFC error.

5. Use a write request queue for Link/Re-Link.

   Link and Re-Link button clicks should create an explicit backend write request containing the selected record id and mode context. The request starts only after the button click, waits for a tag, writes the record id text, then broadcasts exactly one terminal event:
   - success: `{"event":"link_success","data":{"record_id":"<id>"}}`;
   - failure: `{"event":"link_error","data":{"record_id":"<id>"}}`.

   The existing `link_success` persistence behavior should be reused before broadcasting, either by routing through the same helper or by factoring the helper behind both `/events` and real NFC write completion.

   Alternative considered: write as soon as link/re-link mode becomes visible. Rejected because the user explicitly requested write readiness only after the Link/Re-Link button click.

6. Pause standby scanning while a write request is active.

   Even if the frontend returns to standby quickly, the coordinator should avoid overlapping a read poll with a pending write operation. This reduces PN532 contention and prevents the tag being interpreted as a standby scan before the write completes.

## Risks / Trade-offs

- [Risk] Backend mode tracking can become stale if the frontend disconnects or fails to notify mode changes. -> Mitigation: default the coordinator to not polling until a standby mode notification is received, and update mode on initial client connection/render.
- [Risk] Suppressing repeated standby errors may hide a persistent hardware fault. -> Mitigation: log every hardware exception server-side while broadcasting only state changes to the frontend.
- [Risk] Real NFC write success may update persistence while WebSocket clients are disconnected. -> Mitigation: keep using runtime/database state so reconnecting clients receive the current linked state through the existing record fetch and initial events.
- [Risk] Boardless testing and real NFC can both publish events. -> Mitigation: leave `/events` intact and start real NFC background work only when the app is configured for hardware mode.

## Why

Record selection and link/re-link workflows currently depend on simulated or external events instead of the actual NFC tag in the reader field. Real NFC scanning and writing are needed so standby can resolve the record ready to play, and link/re-link actions can persist the selected record id onto a physical tag.

## What Changes

- Add standby-only NFC polling that checks for a tag about once per second.
- Preserve the last successfully scanned record id as the standby record ready to play, even after that tag leaves the reader field.
- Distinguish no-card/no-tag reads from NFC read errors: no tag keeps showing the last valid record when one exists, while read errors surface the standby NFC error state.
- Stop NFC polling whenever the app is not in standby mode.
- Emit standby scan events to the frontend only when the scanned record changes or an NFC read error occurs.
- Make Link and Re-Link actions enter a write-ready state only after the user clicks the Link/Re-Link button; that state waits for a tag to enter the NFC field, then writes the selected record id to that tag.
- Emit link/re-link events to the frontend only for terminal write outcomes: success or failure.
- Keep real NFC event names and payload/status shapes compatible with the existing mock events used for testing.
- Write only the stored record id value to NFC tags, such as `1`, `2`, or another exact application record id.
- Reuse the existing experimental real NFC read/write implementations in `exp/nfc/nfc_read.py` and `exp/nfc/nfc_write.py` as implementation references.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `nfc-library`: Clarify and extend real NFC read/write behavior needed for timeout/no-card handling, read errors, and writing exact record id text values.
- `mode-state-machine`: Define standby-only NFC scan polling behavior, last-valid-record preservation, no-tag handling, read-error handling, and the fact that polling stops outside standby.
- `link-mode-view`: Define that Link/Re-Link waits for a physical tag and completes by writing the selected record id to the tag before emitting success or error outcomes.

## Impact

- Affects the NFC integration layer under the Python runtime/library code that reads and writes PN532 tags.
- Affects boardless/runtime event handling that emits `scan`, `link_success`, and `link_error` events.
- Affects standby, link, and re-link UI behavior through existing mode and link result contracts.
- May require tests or fakes for NFC no-card, read-error, write-success, and write-error cases, plus coverage that polling is active only in standby.

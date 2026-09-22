## Context

The standby NFC coordinator suppresses repeated successful scans by comparing each record ID with `last_emitted_record_id`. When a read fails, it broadcasts the existing null scan payload that puts the frontend into its NFC error state, but it leaves `last_emitted_record_id` unchanged. A later successful read of the same record is therefore suppressed even though the last observable frontend state is now an error.

The existing WebSocket payload contract, frontend scan handler, last-successful-record tracking, and no-card behavior are otherwise suitable and should remain unchanged.

## Goals / Non-Goals

**Goals:**

- Make the first successful NFC scan after an emitted read error recover the frontend.
- Recover when the record ID is the same as before the error and when no-card polls occur between the error and recovery.
- Continue suppressing uninterrupted duplicate successful scans.
- Preserve the last successfully scanned record across no-card polls.

**Non-Goals:**

- Change NFC hardware communication, retry timing, or error classification.
- Change WebSocket event names or payload shapes.
- Change frontend rendering or mode transitions.
- Change link/re-link write behavior.

## Decisions

### Make the remembered emitted record match the observable scan state

When the coordinator broadcasts `{"event":"scan","data":{"record_id":null}}` for a read error, it will clear `last_emitted_record_id`. The frontend no longer displays a record after that event, so retaining the old ID does not represent the emitted state. The next successful record read will consequently be broadcast, while later uninterrupted reads of that same ID will again be suppressed.

Alternative considered: use `scan_error_emitted` to force the next successful read. This is insufficient because the existing no-card path clears that error latch; the common sequence `record -> error -> no card -> same record` would still fail to recover.

### Preserve successful-history and no-card state independently

The change will not clear `last_successful_record_id`. No-card polls will continue to emit nothing and will not modify `last_emitted_record_id`. This keeps the existing distinction between an absent tag and a failed read while allowing an error event to invalidate only duplicate-emission state.

### Cover the complete recovery transition with a coordinator test

A regression test will exercise `same record -> read error -> no card -> same record -> same record`. It will require the event sequence `record -> null -> record`, proving both recovery and renewed duplicate suppression.

## Risks / Trade-offs

- [Risk] A successful read of the same record produces one additional event after an error. → This event is required to replace the frontend error state and is suppressed again after recovery.
- [Risk] Future null scan sources could forget to invalidate duplicate-emission state. → Keep the implementation adjacent to the null error broadcast and encode the behavior in the regression test; a broader scan-state abstraction can be introduced if more scan states are added later.

## Migration Plan

No data or protocol migration is required. Deploy the coordinator and test change together. Rollback consists of reverting the coordinator state update; no persisted data is affected.

## Open Questions

None.

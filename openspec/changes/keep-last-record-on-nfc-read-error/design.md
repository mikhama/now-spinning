## Context

The NFC coordinator polls only in Standby. It currently broadcasts a null `scan` on each new read-error streak and clears the remembered emitted ID, so a later same-ID read is sent again. The UI treats every null `scan` as a transition to Standby's NFC error placeholder, and the server caches that scan for newly connected browsers. Hardware read failures can hide a previously selected Standby record and replay the error on refresh. An externally supplied null scan can separately interrupt Playing because it reaches the same UI handler.

An NFC read that returns an ID is successful even when that ID is unknown or unlinked. The existing not-found view for such IDs remains the resolved scan view.

## Goals / Non-Goals

**Goals:**

- Show one NFC reading error during startup if read failures happen before any successful tag read; no-card polls do not clear that one-time latch.
- Keep the latest resolved Standby scan view and selection on later hardware read failures. Keep Playing and its playback state when an external null scan arrives.
- Seed a reconnecting browser with the latest successful scan or current record after a later externally supplied null scan.

**Non-Goals:**

- Change NFC hardware retries, error classification, polling eligibility, or WebSocket payload shapes.
- Change the not-found behavior for unknown or unlinked IDs or the explicit `#standby-error` preview route.
- Redesign the existing display.

## Decisions

### Latch startup read errors in the coordinator

The coordinator will broadcast one null scan only while no successful NFC ID has been read during this process. A no-card result will leave the startup error latch intact. A successful read records its ID and continues the existing changed-ID duplicate suppression. Later read failures will be logged but will not clear the remembered ID or broadcast a null scan. This also removes an unnecessary repeat scan of the same record after a transient read failure.

Alternative considered: keep broadcasting null after every error streak and depend entirely on the UI to ignore it. That would still cache an error for a reconnecting browser and force each client to recover its own history.

### Make the frontend resilient to null scan events

The UI will remember whether it has resolved a non-null scan during this browser session. A first null scan before that point enters the startup NFC error view once. Later null scans leave state and mode untouched. A non-null scan continues the existing linked or not-found resolution. A valid `current_record` seed also counts as an established record. This covers boardless events during Playing and reconnect races.

Alternative considered: use `currentRecordId` as the guard. An unknown or unlinked scan clears that ID even though the NFC read succeeded; a following read error would then incorrectly replace Record Not Found with NFC Reading Error.

### Preserve the server's reconnect snapshot

When an externally supplied null scan arrives after a non-null scan or established `current_record`, the server will broadcast the event to connected clients but retain its previous successful scan snapshot. Before any success, it will retain the first null scan for initial browser connections. This keeps initial state aligned with what connected clients display without introducing a new event or persistent storage.

Alternative considered: replay both the successful scan and subsequent null error to reconnecting clients. That adds avoidable transitions and relies on replay order to reconstruct the intended view.

## Risks / Trade-offs

- [Risk] Read failures after a successful scan are no longer visible in the record area. → Keep error logging in the coordinator; the UI is intentionally stable.
- [Risk] An unknown or unlinked successful scan remains the latest resolved view. → Preserve the existing Record Not Found behavior rather than resurrecting an older linked record after a later read failure.
- [Risk] Browser-only history is lost on refresh. → The server's retained scan snapshot seeds the refreshed browser with the latest resolved view.

## Migration Plan

No protocol or data migration is required. Deploy coordinator, server, and frontend changes together. Reverting the code restores the former error transitions; process-local runtime state resets on restart.

## Open Questions

None.

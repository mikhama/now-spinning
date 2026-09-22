## Context

Standby scans use one WebSocket event shape for both successful NFC reads and read failures. A successful read carries the decoded `record_id`; a read failure carries `record_id: null`. The coordinator currently checks whether the decoded ID is linked and replaces an unlinked ID with `null`, which erases the evidence that the NFC read succeeded. The frontend consequently follows its null-payload branch and renders “NFC Reading Error.”

The frontend already has the collection and each record's `linked` state. It also already maps an unknown non-null scan ID to “Record Not Found,” so it can resolve both unknown and unlinked IDs without expanding the event protocol.

## Goals / Non-Goals

**Goals:**

- Keep `record_id: null` exclusively associated with NFC read failures.
- Send the decoded ID for every successful standby tag read.
- Show “Record Not Found” and avoid activating metadata when the decoded record is unknown or unlinked.
- Preserve existing duplicate-scan suppression, no-card behavior, and recovery after a read error.

**Non-Goals:**

- Changing NFC tag contents, database linkage rules, or the link/re-link workflow.
- Adding a new WebSocket event type or payload discriminator.
- Changing the visual treatment of either existing error placeholder.

## Decisions

### Successful reads always carry the decoded record ID

The coordinator will no longer translate an unlinked record ID into `null`. Once NFC decoding succeeds, it will run the normal successful-read path, broadcast the non-null ID when required by duplicate suppression, and track that ID as the last successful/emitted scan.

This keeps the transport semantic precise: `null` means the reader could not produce an ID, while a string means the reader did produce one. Adding a new `reason`, `linked`, or event-type field was considered, but it would unnecessarily widen a protocol that can already express the distinction.

### The frontend resolves scan eligibility from its record state

The scan handler will activate a record only when the matching collection entry exists and is linked. A non-null ID that is missing or has a false `linked` value will clear the active record with the existing `not-found` state. Other activation paths remain unchanged.

The coordinator currently receives a database linkage callback only to collapse unlinked reads into the error payload. That dependency will be removed from the scan path because linkage is a presentation/application-state decision, not an NFC-read result.

### Existing scan latching remains unchanged

An unlinked ID participates in the same last-emitted-ID suppression as any other successfully decoded ID. Keeping the tag in the reader field will not generate repeated events. A real read error still clears the emitted-ID latch so the same tag can be emitted again after recovery.

## Risks / Trade-offs

- [Risk] The frontend's in-memory `linked` value could be stale after an out-of-band database update. → Existing sync refreshes and `link_success` events update that same state; no new consistency mechanism is introduced by this fix.
- [Risk] Treating unlinked IDs as successful reads changes coordinator bookkeeping. → Focused tests will cover payloads, duplicate suppression, and recovery to ensure only the user-facing classification changes.

## Migration Plan

Deploy the coordinator and frontend changes together. No data migration is required. Rollback consists of reverting both code changes; stored NFC tags and database rows remain compatible.

## Open Questions

None.

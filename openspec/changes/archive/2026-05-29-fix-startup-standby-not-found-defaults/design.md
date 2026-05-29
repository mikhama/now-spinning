## Context

The frontend currently initializes in standby mode and later seeds `currentRecordId` from the first fetched record when no explicit runtime event has selected a record. That makes a cold app load look like a real record is already active, even though the intended workflow is NFC-driven. The same initialization path also leaves the first rendered side label vulnerable to missing data or inconsistent fallback handling.

This change touches the shared UI state model in `ui/app.js`, specifically initialization, hash-based debug routing, scan/current-record event handling, and standby/play rendering. Existing README hash routes must remain useful for debugging individual views.

## Goals / Non-Goals

**Goals:**
- Make a cold load with no hash render the standby not-found view instead of auto-selecting the first record.
- Ensure a record becomes visible only after scan-driven state chooses a valid record.
- Ensure the first displayed side is deterministic and renders as Side A for newly loaded records.
- Preserve existing debug hash routes and existing standby error semantics for NFC and unknown-record scans.

**Non-Goals:**
- Redesign standby error visuals or copy.
- Change link, re-link, sync, or stylus behavior outside shared initialization side effects.
- Introduce a new top-level mode for pre-scan idle state.

## Decisions

### Reuse the existing standby not-found state for pre-scan startup
Use `mode = "standby"`, `standbyError = "not-found"`, and `currentRecordId = null` as the cold-start state when the app loads without a hash. This avoids adding a new mode or placeholder type while matching the requested first-screen behavior.

Alternative considered: add a separate `pre-scan` or `idle` standby sub-state. Rejected because it would add rendering and state-machine surface for behavior that is intentionally identical to the existing not-found layout.

### Stop deriving the current record from fetched records on normal startup
Fetched records should populate browseable data only; they should not implicitly select the first record as active application state. The active record should come from scan or explicit runtime events.

Alternative considered: keep seeding `currentRecordId` and special-case only the initial render. Rejected because it preserves hidden stale state that can leak into later mode transitions.

### Preserve hash-based debug routing as an explicit override path
Cold-load behavior changes only when no hash is present. Existing hash routes remain an explicit developer override so preview routes like `#standby`, `#play`, and error hashes still work for README-driven debugging.

Alternative considered: make all startup paths, including hashes, begin in standby-not-found. Rejected because it would reduce the usefulness of current debug routes and conflict with the existing UI-app requirement that hash-based dev routing remain functional.

### Normalize initial side display from the first available side
Whenever a record becomes active through scan or current-record events, side state resets to index `0`, and rendering should label that first visible side deterministically. If a side object is missing an `id`, rendering should fall back to `A` for the first side rather than surfacing `undefined`.

Alternative considered: trust the API data and only reset the side index. Rejected because the reported UI defect is in rendered output, so the render path needs a defensive fallback as well.

## Risks / Trade-offs

- [Risk] Reusing `standbyError = "not-found"` for both pre-scan and true not-found scans blurs those two causes internally. → Mitigation: keep the reuse limited to startup, and rely on the shared placeholder because the requested visual behavior is identical.
- [Risk] Removing implicit first-record selection could affect any mode that assumed `currentRecordId` is always populated. → Mitigation: update standby/play rendering to tolerate `null` current records and verify hash preview routes still seed record display when requested.
- [Risk] Side-label fallback to `A` could mask malformed upstream data. → Mitigation: limit fallback to presentation only and keep the underlying side data unchanged.
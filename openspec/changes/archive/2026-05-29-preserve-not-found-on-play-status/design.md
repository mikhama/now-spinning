## Context

The frontend already models a record-not-found standby state with `currentRecordId = null` and `standbyError = "not-found"`. When a `status: "play"` event arrives, the WebSocket handler currently switches `mode` to `"play"` without changing record state. That is reasonable for transport status, but the play view and action-bar selection both assume a valid current record exists. The result is a play screen that can expose stale metadata or controls even though no record was successfully resolved.

This change is limited to the UI state and rendering contract in `ui/app.js` and the corresponding play-mode markup in `ui/index.html`. Existing hash-based debug routes, especially `#play`, must keep working as explicit developer overrides that seed a visible record.

## Goals / Non-Goals

**Goals:**
- Preserve the runtime not-found context when playback starts without a valid current record.
- Define an explicit play-mode empty state that shows the record-not-found placeholder instead of stale artwork or metadata.
- Ensure the play action bar shows no buttons when the play fallback is active.
- Keep normal play behavior unchanged when a valid scanned record exists.

**Non-Goals:**
- Redesign placeholder visuals or wording.
- Change scan, `current_record`, or hash-preview behavior beyond what is needed to support the play fallback.
- Introduce new backend events, APIs, or persisted state.

## Decisions

### Keep `mode = "play"` even when no record is available
The status event should continue to represent platter state, so the app should still enter play mode when the turntable starts. The fix is to preserve the null-record context instead of fabricating a default record.

Alternative considered: ignore `status: "play"` when no active record exists. Rejected because it would hide the real runtime state transition and make the top-bar mode label inconsistent with the incoming status event.

### Add an explicit play fallback render path
Play mode needs its own empty-state rendering contract. The fallback should reuse the same "Record Not Found" placeholder pattern as standby, but it should remain inside the play section so the mode label and section selection stay aligned with play mode.

Alternative considered: reuse the standby section whenever play has no record. Rejected because it couples section visibility to error state and would make the UI appear to leave play mode even though the transport status says otherwise.

### Hide the action bar when play has no valid record
When play is active without a valid current record, the app should not activate the normal play controls and should not substitute standby controls. The absence of any active action group matches the requested behavior of showing no buttons at all.

Alternative considered: show disabled prev/next/side controls or fall back to the standby Mode button. Rejected because both options imply an actionable record context that does not exist.

### Preserve hash-based `#play` preview behavior as an explicit override
The existing dev route that enters `#play` with the first record loaded remains useful for previewing the full play layout. The new fallback applies only to runtime play transitions where no valid current record exists.

Alternative considered: make all play paths, including `#play`, use the empty fallback until a scan arrives. Rejected because it would remove a documented debug route from the README workflow.

## Risks / Trade-offs

- [Risk] A play fallback with no action bar removes the Mode button temporarily. -> Mitigation: keep this behavior scoped to the no-record play fallback, and rely on the next scan or stop event to return to an actionable state.
- [Risk] Reusing the record-not-found placeholder in play mode could blur whether the missing record came from startup, a failed scan, or some other null-record path. -> Mitigation: keep the fallback purely presentational and avoid inventing a new error subtype unless later requirements demand it.
- [Risk] `current_record` events can preload a record without making it visible in standby. -> Mitigation: define the play fallback based on whether a valid current record resolves at render time, not on standby visibility flags.
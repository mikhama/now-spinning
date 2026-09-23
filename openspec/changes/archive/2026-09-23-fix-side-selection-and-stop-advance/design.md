## Context

The browser holds the selected record, side, track, and boardless playback correction in `ui/app.js`. A null NFC scan currently clears all of them, and every later scan resets side and track even when it identifies the same record. Stop advancement uses only the final 20 seconds of the estimated side. Empty Link mode reuses the Standby action group, whose Side button may remain visible from the previous screen.

## Goals / Non-Goals

**Goals:**

- Preserve record identity and side selection through a transient NFC read error and recovery of the same linked record.
- Reset side selection when a different linked record is scanned or the previous record is invalidated by an unknown or unlinked scan.
- Advance one side once on stop after at least 60 seconds of raw playback, or near/past a known estimated side end.
- Keep a manual side change effective during Play and later elapsed-time updates.
- Give empty Link, Re-Link, and Stylus states their own Mode-only action group.

**Non-Goals:**

- Persist side selection across a browser reload or device restart.
- Change NFC polling, scan payloads, or record storage.
- Redesign the fixed-size touchscreen interface.

## Decisions

### Separate a transient NFC error from record identity

A null scan will set the NFC error presentation and hide the Standby record, but retain the last valid record ID and side selection. The next successful linked scan will compare its ID with the retained ID. Only a different ID resets side, track, and boardless timing. An unknown or unlinked scan still clears the active record. This preserves the user's side choice through the observed error/retry sequence while keeping invalid scans in the existing not-found state.

### Use elapsed playback as a second stop condition

The stop handler will advance if raw elapsed playback is at least 60 seconds, or if effective playback has reached the final 20 seconds of a side with a positive estimated duration. Raw elapsed time is used for the minute rule so a manual playback correction cannot make a short run look long. The stop transition will still reset the selected track and clear Play-only timing, and duplicate stop events cannot advance twice because the second finds Standby mode.

### Rebase Play-mode manual side corrections

For a normal side switch, preserve the selected track index where possible and set the playback correction to that track's start. After an estimated side overrun, preserve the effective position relative to the previous side when moving to the next side. Use the existing correction setter so the offset is always relative to the latest raw elapsed time. The selected side remains explicit until another Side click or a qualifying stop.

### Reuse the existing action button component for empty states

Add a Mode-only action group using the current four-column grid and button style. Route empty Link, Re-Link, and Stylus states to it. Its Mode button uses the existing mode-cycle handler. No new visual tokens or page layout are needed.

## Risks / Trade-offs

- [Risk] A transient read error leaves a valid record in memory while an error screen is shown. → Mitigation: hide the Standby record and Side button until a valid scan clears the error; clear identity on unknown or unlinked scans.
- [Risk] The one-minute rule can advance before an unusually long side is finished. → Mitigation: apply it only on a real stop event and use the measured raw elapsed duration, as requested.
- [Risk] Estimated track durations can be missing. → Mitigation: require a positive estimate for the final-20-second rule; the one-minute rule still works.

## Context

The SQLite schema already stores `stylus.active`, but imports default every new row to active. The tracker lazily chooses the first active ID, the UI navigates only in memory, and its compact bar uses the first response row. The offline CLI already uses existing-only SQLite transactions and requires a stopped app.

## Goals / Non-Goals

**Goals:** Make one persisted selection authoritative across restart, sync, API, navigation, and usage tracking. Reject activation during backend playback and safely delete inactive entries offline.

**Non-Goals:** Schema changes, a UI redesign, remote collection deletion, new event formats, online CLI coordination, spec sync, or archival.

## Decisions

1. Reuse `active`. Initialization normalizes legacy flags transactionally: retain the first active ID in the existing ID order, or select the first ID if none is active. Only flags change. Return styli in stable text-ID order with boolean flags. Sync normalizes the existing selection before inserting inactive rows, then normalizes again so an initially empty collection acquires one selection. Remote flags and hours cannot replace local state. A new selection column or table would duplicate existing state.
2. Add an existing-database selection transaction that verifies the target, updates all flags, and returns the selected ID and saved hours only after commit. Missing targets do not mutate rows. Keep deletion's target lookup, effective active-selection check, and delete in one `BEGIN IMMEDIATE` transaction. Legacy active ambiguity uses the same effective selection rule; reject that selected ID with `ValueError`.
3. Serialize backend status transitions, tracking, and activation with the tracker's reentrant lock. Check backend runtime `status == play` before any selection or tracking work. Under that lock, validate the target, treat the current selection as a no-op, flush remaining previous pending hours, commit selection, load the returned hours, and clear the elapsed baseline. Flush failures abort selection; a later selection-write failure can leave previously pending hours durably saved, but never credited to the new stylus. Hold the lock through flush persistence as well to prevent duplicate concurrent flushes.
4. Add `POST /styli/<id>/activate`: JSON success after commit; JSON 404 for missing targets, 409 during playback, and 500 for persistence failure. Keep mock data flags consistent; activation applies only to persisted rows.
5. Adapt the existing stylus controls and both existing wear bars. Initialize the selected index from `active` after sorting by ID. Prev/Next sends the adjacent ID with wraparound and changes local selection only on confirmed success. Track received playback status separately from mode and hash routing. Disable navigation for playback or pending requests. On failure, replace stylus details with a generic `An error occurred!` message using the existing empty-state class and `role=alert`; hide Reset and keep Prev/Next available while stopped. Do not show a banner or separate Retry button. A lost response automatically reloads saved selection. If that reload fails, the next Prev/Next click reloads it before choosing and persisting the adjacent ID, keeping controls disabled throughout recovery and activation. Recheck playback after recovery. Invalidate older in-flight reads when activation succeeds so they cannot restore stale flags.
6. Extend the standard-library CLI with `delete <id>`, reporting success only after commit. Add active state to `list` after existing columns to help operators identify protected entries. Document selecting another stylus while playback is stopped, then exiting normally and waiting for the app to stop before deletion. Reimport through collection sync starts a deleted row at zero hours.

## Risks / Trade-offs

- SQLite writes hold the tracker lock → keep work local and bounded; never hold it for WebSocket network sends.
- Lost activation responses leave uncertain client state → refetch saved flags and guard mutations until recovery succeeds.
- CLI has no application lock → require the established stopped-app procedure in README and every command's help.
- Local deletion can be undone by sync → explicitly document reimport at zero hours.

## Migration Plan

No schema migration is required. On first application database initialization, normalize legacy flags while preserving metadata and totals. Validate with temporary databases, restart simulations, thread-controlled races, API requests, UI tests, CLI subprocesses with `python -S`, and strict OpenSpec validation. Leave this change open and main specs unchanged.

## Open Questions

None.

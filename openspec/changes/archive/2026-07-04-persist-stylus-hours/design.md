## Context

The backend already detects playback from platter RPM and publishes `status` events once per elapsed playback second. The frontend consumes those events for play mode and separately consumes `stylus_hours` events to update the wear bar. Today `stylus_hours` is only runtime state except for manual reset, while the persistent source for stylus usage is `stylus.distance_hours` in SQLite.

The app runs as a Flask process launched by `bin/run_kiosk.sh`. Kiosk exit currently calls `/kiosk/exit`, which asks the parent runner to terminate, and the runner then kills the app process during cleanup. Unexpected power loss cannot be made perfectly safe, but the app can limit loss to the interval since the last committed SQLite write and make graceful exits flush pending usage first.

## Goals / Non-Goals

**Goals:**
- Count active stylus playback time from backend playback status rather than from browser timers.
- Keep live UI hours updated while a record is playing.
- Persist accumulated usage to SQLite at least every 10 minutes, on playback stop, and before kiosk exit requests process termination.
- Use database writes that commit the updated `distance_hours` value with SQLite durability settings suitable for local power-loss recovery.
- Keep the current REST/WebSocket contracts intact where possible.

**Non-Goals:**
- Add a stylus replacement workflow, usage history, or played-album log.
- Persist stylus selection changes in the UI.
- Backfill lost hours from previous app runs.
- Guarantee recovery for seconds that were only in memory and never committed before a sudden power loss.

## Decisions

### 1. Add a backend stylus-hours tracker

Introduce a small backend component responsible for stylus-hour accrual. It should receive status messages before or as they are broadcast, inspect `status: "play"` and `status: "stop"`, and maintain:

- active stylus ID
- current in-memory hours for that stylus
- last observed playback elapsed seconds
- pending unflushed seconds
- last flush time/threshold state

Rationale: playback truth already lives in the backend, and the browser can disconnect, reload, or run in hash-based dev mode. Counting in the frontend would make persistence depend on a UI session instead of the hardware detector.

Alternative considered: POST stylus-hour increments from the browser during play mode. Rejected because it couples durable accounting to frontend lifecycle and can miss kiosk/browser crashes even when the backend is still running.

### 2. Use the active database stylus as the counted stylus

Resolve the counted stylus from the existing `stylus.active` ordering/source. For this change, the active stylus is the first active row returned by the database. If no stylus exists, the tracker should skip accrual and log/debug the condition rather than creating a partial row.

Rationale: the database already contains an `active` field and `get_all_styli()` orders active styli first. This avoids inventing a second source of truth. A later change can make Prev/Next persist active selection explicitly.

Alternative considered: count against the frontend-selected stylus. Rejected for now because selection is not persisted and the backend cannot trust a browser-only value after reconnects or graceful shutdown.

### 3. Increment persisted hours instead of overwriting absolute hours

Add database helpers for:

- reading the active stylus with current hours
- incrementing a stylus by a delta in hours

The durable write should be an additive update such as:

```sql
UPDATE stylus
SET distance_hours = distance_hours + ?
WHERE id = ?
```

Rationale: incrementing only the accumulated delta reduces the risk of overwriting a reset or another update with a stale absolute value. It also keeps the tracker's responsibility clear: it owns pending seconds, not the whole stylus row.

Alternative considered: update `distance_hours` to the tracker's absolute in-memory value on every flush. Rejected because it is more sensitive to stale cache if reset or sync-related data changes happen while playback is active.

### 4. Flush on interval, stop, and graceful exit

The tracker should flush pending seconds when any of these happen:

- pending playback reaches 600 seconds
- a `status: "stop"` message arrives
- `/kiosk/exit` is accepted
- process shutdown hooks run, where feasible

Rationale: the 10-minute interval caps expected power-loss exposure, while stop and graceful exit cover normal listening sessions and planned shutdowns. A process signal/atexit hook is a backup for runner cleanup, but `/kiosk/exit` is the most reliable graceful app-level hook because it runs before the runner is asked to terminate.

Alternative considered: only flush every 10 minutes. Rejected because many plays/sides are shorter than 10 minutes, and a clean exit after short playback would still lose all pending usage.

### 5. Broadcast live `stylus_hours` after in-memory updates

When status events advance playback time, the tracker should update in-memory hours and broadcast or return a `stylus_hours` event with the current total. This preserves the existing UI contract and keeps the wear bar moving even before the next database flush.

Rationale: the UI already understands `stylus_hours` events. Reusing that event keeps frontend changes minimal and avoids polling.

Alternative considered: only update UI after database commits. Rejected because hours would appear stale for up to 10 minutes during playback.

### 6. Tighten SQLite durability for committed writes

Keep WAL mode, but set synchronous behavior explicitly for durability-sensitive writes. The database connection should use `PRAGMA synchronous=FULL` or an equivalent durable setting so a committed stylus-hour flush has strong local disk persistence semantics.

Rationale: the user specifically wants confidence that database writes are actually stored on disk in case of voltage or shutdown problems. SQLite commit durability depends on synchronous settings and filesystem behavior.

Alternative considered: keep default synchronous settings. Rejected because defaults are less explicit and make the durability contract harder to reason about.

## Risks / Trade-offs

- [Risk] Sudden power loss can still lose unflushed in-memory seconds. -> Mitigation: flush at least every 10 minutes and on normal stop/exit; document that the maximum expected loss is the current pending interval.
- [Risk] Multiple active styli would make the counted stylus ambiguous. -> Mitigation: use the first active stylus by existing ordering for this change, and leave strict active-stylus enforcement to a future selection-persistence change.
- [Risk] Extra SQLite commits during playback could add small I/O overhead on Raspberry Pi storage. -> Mitigation: flush in batches rather than every second.
- [Risk] Reset during active playback can race with pending deltas. -> Mitigation: reset should clear runtime hours and pending seconds for that stylus, and future increments should start from the reset value.

## Migration Plan

No schema migration is required because `stylus.distance_hours` already exists. Existing databases should continue to load unchanged.

Rollback is straightforward: removing the tracker returns behavior to transient runtime updates plus manual reset persistence, with already-committed `distance_hours` values remaining valid.

## Open Questions

- Should there be exactly one active stylus enforced in the database, or is first-active ordering acceptable until stylus selection persistence is implemented?
- Should interval flushes happen every fixed 600 playback seconds, every 600 wall-clock seconds while playing, or both? Playback seconds are the cleaner accounting unit for this change.

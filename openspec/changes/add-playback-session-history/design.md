## Context

SQLite stores collection rows and local stylus totals. `StylusHoursTracker` counts playback-counter deltas under its reentrant lock; `broadcast_message` shares that lock with stopped selection. Saves occur periodically, on stop, selection, power actions, and cleanup. Console tools must remain usable without Flask or hardware dependencies.

## Goals / Non-Goals

**Goals:** Durable known-record history independent of styli, safe retries, one readable console report, narrowly confirmed deletion, and additive initialization.

**Non-Goals:** Reconstructing past playback, UI or HTTP additions, automatic clearing while the app runs, spec sync, or archive.

## Decisions

1. Add `sessions_log(id INTEGER PRIMARY KEY, record_id TEXT NOT NULL, session_started_at TEXT NOT NULL, session_duration_sec INTEGER NOT NULL CHECK (...))` through `CREATE TABLE IF NOT EXISTS`. Enforce positive integer durations. Write UTC ISO 8601 timestamps with `+00:00`. Do not cascade metadata deletion into history: names are joined when reporting. Reusing stylus hours cannot express record history.
2. Use a separate tracker under the existing playback lock. Resolve nonempty record IDs against `record`; establish a fresh counter baseline on record changes or first resolution so unknown time is never assigned retroactively. A positive counter delta starts an interval at the observation's UTC time minus that delta. Stop, record change, and counter reset close segments. Checkpoints advance an open segment's start by the committed duration; they do not start it again at wall-clock time.
3. Keep closed segments in order, with one open segment. Save a snapshot of all unsaved segments in one SQLite transaction. Only dequeue and advance after commit. Failed transactions retain all pending seconds; successful saves leave nothing to duplicate on repeated cleanup. An all-or-nothing batch avoids partially acknowledged writes.
4. Defer stylus persistence during coordinated event handling while retaining standalone tracker defaults. Process both trackers independently, then attempt both saves on stop and stylus periodic checkpoints. Also checkpoint history every 600 counted seconds, including when no stylus exists. Valid stopped selection saves both before changing stylus; same-active selection remains a no-op. A stylus reset changes only the stylus tracker. Exit and Shut Down abort on either failure. Cleanup freezes playback accounting and permits a later cleanup call to retry failed saves without rerunning NFC cleanup.
5. Implement one executable backed by standard-library modules. Report committed rows through an existing read-only database connection, sorted by UTC timestamp then primary key. Group only adjacent matching local record IDs, sum durations, and retain the first start. A left join preserves missing metadata. Format local offset-aware time and unbounded hours with Unicode-aware column padding. Clear uses an existing database, exact untrimmed confirmation, and one delete transaction. Neither command initializes or upgrades the schema.

## Risks / Trade-offs

- Abrupt power loss can lose the last uncommitted interval → save at existing checkpoints plus 600 history seconds; no claim of reconstructing unsaved playback.
- A record change between counter observations has no exact counter timestamp → discard that ambiguous crossing interval by establishing a new baseline.
- Wall-clock corrections can change chronological report order → store UTC-aware timestamps and sort by timestamp with ID tie-breaks as requested.
- No cross-process application lock for clear → document normal Exit, wait, clear, restart. Reporting can run while playback continues and shows committed rows only.

## Migration Plan

Normal app initialization adds the table without deleting the database. Collection upserts leave history untouched. Console tools reject missing databases or schemas. Rolling back app code can leave the unused additive table intact. Keep this OpenSpec change open after validation.

## Open Questions

The request refers to a supplied example without supplying its source rows. Validation will use an explicit fixture totaling 1,234 and 245 seconds, and record its constituent entries.

## Context

`api/services/db/database.py` stores usage as SQLite `REAL` in `stylus.distance_hours`. Connections use WAL and FULL synchronous durability. The application accumulates playback usage in memory and flushes it on stop and normal exit. Collection sync uses `INSERT OR IGNORE` for styli, preserving existing rows but importing remote hours into new rows. The reset API currently has its own SQL update.

## Goals / Non-Goals

**Goals:**

- Provide executable list/set/reset commands for the existing project database using only the Python standard library.
- Persist an absolute finite, nonnegative total atomically and report its previous value after commit.
- Make local hours authoritative across application restart and collection sync.
- Preserve the existing reset API contract and runtime reset behavior.

**Non-Goals:**

- Application locking, process detection, remote Pi access, schema changes, UI changes, new HTTP endpoints, or modifications to `my-musical-journey`.
- Syncing OpenSpec delta specs or archiving this change.

## Decisions

1. **Small Python entry point and isolated CLI module.** `bin/stylus-hours` locates the project root and delegates to `api/stylus_hours_cli.py`. Import the database module directly without importing the Flask app or hardware modules. This reuses the database layer without requiring application dependencies or a running server; invoking the HTTP API would violate the offline workflow.
2. **Explicit existing-file connection mode.** Add an opt-in existing-only path to the database connection helper using SQLite URI `mode=rw`. The CLI uses this for list and updates and never calls `init_db()`. Keep the app's auto-creation behavior. A filesystem existence check alone would still allow accidental creation if the file disappears before connection.
3. **Shared absolute-total operation.** `set_stylus_hours` validates the value without rounding, starts a SQLite write transaction before reading the old total, updates only the matching stylus, and returns previous/new totals after commit (or no result for a missing stylus). A failed commit rolls back. `reset_stylus_hours` delegates to it with zero and retains its boolean return for API callers. Ordinary SQLite transaction locking is required for atomicity; there is no application lock.
4. **Enforce local ownership at the database boundary.** Insert new styli with literal zero regardless of remote `distance_hours`, retaining `INSERT OR IGNORE` for existing rows. Keeping enforcement here also covers callers that bypass extraction; stripping the JSON field alone would not.
5. **Stopped-app procedure.** Put the prerequisite in command help and the README: exit normally, wait for the app to stop, list, set/reset, then restart. There is no prompt or automatic process control. On a new Pi, sync before setting the initial value.

## Risks / Trade-offs

- [Running the tool while the app holds pending usage changes the requested total later] → Require the stopped-app procedure explicitly; provide no application lock as requested.
- [SQLite REAL cannot represent every decimal exactly] → Use the same floating-point representation as playback tracking, with no display or storage rounding introduced by the CLI; test equality with the parsed input.
- [Missing or incompatible database, permissions, or a failed write] → Report the error to stderr, return nonzero, and print no success message before commit.
- [A new Pi starts at zero despite a legacy remote total] → Document syncing first and then setting its initial local total.

## Migration Plan

Deploy the updated project without deleting or recreating existing databases. Existing totals survive unchanged. Operators can remove `distance_hours` from collection JSON independently. Rollback requires reverting code only; no schema migration is involved, though older code again imports hours for new rows.

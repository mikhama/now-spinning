## Context

The frontend reset button already calls `POST /styli/<id>/reset` and then updates local UI state to show `0` hours. The backend endpoint currently returns `{ "success": true }` without changing `data/now-spinning.db`, so the reset is lost once data is reloaded from persistent storage.

The SQLite schema stores stylus usage in `stylus.distance_hours`. Existing database write helpers live in `api/services/db/database.py`, including `mark_record_linked(record_id)`, which returns whether a row was updated.

## Goals / Non-Goals

**Goals:**
- Persist a stylus reset by setting `stylus.distance_hours` to `0`.
- Return success only when a matching stylus row was updated.
- Return 404 when the requested stylus does not exist.
- Keep the existing frontend endpoint contract and button flow.

**Non-Goals:**
- Change stylus capacity fields, active stylus selection, or sync import behavior.
- Add user confirmation or new reset UI states.
- Broadcast a new WebSocket event after reset.

## Decisions

1. Add a database helper named around the operation, such as `reset_stylus_hours(stylus_id)`, in `api/services/db/database.py`.

   Rationale: This keeps SQL writes in the database layer and mirrors the existing `mark_record_linked(record_id)` pattern. The endpoint can stay thin: initialize the database, call the helper, map `False` to 404, and return success otherwise.

   Alternative considered: Execute SQL directly in `api/main.py`. This would work for a small change, but it would duplicate connection handling and weaken the existing separation between routes and persistence helpers.

2. Use `UPDATE stylus SET distance_hours = 0 WHERE id = ?` and return `cursor.rowcount > 0`.

   Rationale: The request is explicitly to reset hours in the database to zero. `rowcount` gives the endpoint a clear way to distinguish existing and missing styli.

   Alternative considered: Upsert a missing stylus with zero hours. Rejected because reset should only affect known styli; creating partial stylus rows would risk corrupting collection data.

3. Keep frontend optimistic UI behavior after successful response.

   Rationale: The frontend already waits for an OK response before setting the selected stylus hours to `0`. Once the endpoint persists the reset, this behavior remains correct without UI changes.

   Alternative considered: Refetch styli after reset. Rejected for this change because the endpoint response already confirms persistence, and existing UI state updates are scoped and fast.

## Risks / Trade-offs

- [Risk] Existing installations may not have a synced stylus row yet. -> Mitigation: call `init_db()` before reset and return 404 if no row exists.
- [Risk] Mock in-memory `STYLI` data may remain non-zero after a database reset. -> Mitigation: keep the source of truth for this behavior in SQLite; frontend state already updates to `0` after success, and future API read alignment can be handled separately if needed.

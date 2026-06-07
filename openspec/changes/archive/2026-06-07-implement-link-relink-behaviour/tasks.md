## 1. Persistence and API

- [x] 1.1 Add a database helper that sets `record.linked = 1` by record ID and reports whether a row was updated.
- [x] 1.2 Update `POST /records/<id>/link` to use the database helper, persist linked state, and return 404 for missing records.
- [x] 1.3 Update `POST /events` so `link_success` validates `data.record_id`, persists the linked state before broadcast, returns 400 for missing IDs, and returns 404 for unknown records.
- [x] 1.4 Keep `link_error` accepted by `POST /events` with `data.record_id` and broadcast it to connected WebSocket clients.

## 2. Link/Re-Link UI State

- [x] 2.1 Add UI state for pending link record/mode and clear it on mode changes or new link attempts as appropriate.
- [x] 2.2 Update Link and Re-Link button handlers to start pending state instead of immediately marking records linked.
- [x] 2.3 Render the sync-style blinking dot under the linked/not-linked label while the selected record has a pending link.
- [x] 2.4 Handle `link_success` WebSocket events by clearing pending/error state and marking the matching client-side record as linked.
- [x] 2.5 Handle `link_error` WebSocket events by clearing pending state and showing the link error state in link or re-link mode.

## 3. Filtering, Navigation, and Empty States

- [x] 3.1 Ensure link mode displays only unlinked records and removes successfully linked records from navigation after the user presses Prev or Next.
- [x] 3.2 Ensure repeated link-mode success flows eventually show the `No unlinked records` empty state with only the Mode action.
- [x] 3.3 Ensure re-link mode displays only linked records, keeps successfully re-linked records reachable, and wraps Prev/Next within linked records.
- [x] 3.4 Add or update the re-link empty-state UI to show `No linked records` with only the Mode action when there are no linked records.
- [x] 3.5 Remove any dev/demo logic that force-marks all records linked when entering re-link mode.

## 4. Verification

- [x] 4.1 Add or update backend tests for database linked-state updates, `POST /records/<id>/link`, and `POST /events` `link_success` validation/persistence.
- [x] 4.2 Add or update frontend tests, or manual deterministic checks, for pending indicator, `link_success`, `link_error`, link-mode disappearance after navigation, and re-link persistence.
- [x] 4.3 Verify boardless curl examples for `link_success` and `link_error` against a running app and document the exact commands in implementation notes or test output.

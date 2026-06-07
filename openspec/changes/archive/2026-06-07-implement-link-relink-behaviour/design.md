## Context

The app already has link and re-link screens, a `linked` flag in record data, and a boardless `/events` endpoint that broadcasts injected events over WebSocket. Link mode currently filters unlinked records in the UI, but the end-to-end link workflow still needs a pending state, a boardless NFC/tag completion event, persistence of successful links, and empty-state behavior for both link and re-link modes.

This change is for boardless mode only. Hardware NFC writing can later produce the same success/error event shapes.

## Goals / Non-Goals

**Goals:**

- Browse only unlinked records in link mode and only linked records in re-link mode.
- Show a pending link indicator after the user clicks Link/Re-Link while waiting for tag completion.
- Support curl-injected link success and link error events for boardless testing.
- Persist successful link results by setting the record's `linked` flag to true.
- Keep successfully linked records out of link mode once the user navigates away, while keeping them visible in re-link mode.
- Show empty states with `No unlinked records` and `No linked records`.

**Non-Goals:**

- Real NFC hardware write integration.
- Tag ID storage or mapping between records and physical tag UIDs.
- Unlinking records or changing a linked record back to unlinked.
- Full database migration automation beyond adding/update helper behavior expected by the current schema.

## Decisions

### 1. Use explicit boardless link result events

Add two boardless event shapes:

- `{"event":"link_success","data":{"record_id":"1"}}`
- `{"event":"link_error","data":{"record_id":"1"}}`

The existing `/events` endpoint remains the injection surface, so manual testing uses curl and connected UI clients receive the same WebSocket events. `record_id` is required for success so the server and UI update the same record deterministically.

Alternative considered: overload `scan` events. Rejected because scan currently means "a tag was read and maps to a record"; link completion is a separate write/association workflow and needs different UI handling.

### 2. Persist success on the server before broadcasting

When `/events` receives `link_success`, the API server updates the matching database record to `linked = 1` and then broadcasts the event. If the record does not exist or cannot be updated, the server responds with an error and does not broadcast a misleading success.

Alternative considered: let the UI mark the record linked locally and refresh later. Rejected because successful link state must survive navigation, refreshes, and other clients.

### 3. Keep pending link state local to the UI

Clicking Link/Re-Link sets UI state such as `pendingLinkRecordId` and `pendingLinkMode`, clears any prior link error, and renders the same blinking dot visual used by sync mode below the status label. The UI leaves the selected record visible while pending.

On `link_success`, the UI clears pending state, clears the error, marks the matching in-memory record `linked = true`, and re-renders. On `link_error`, the UI clears pending state and shows the existing link error state for the current link/re-link mode.

Alternative considered: make the Link button call `/records/<id>/link` directly. Rejected for this workflow because the requested interaction waits for an NFC/tag event and should be testable with boardless event injection.

### 4. Navigation controls determine when link mode drops a successful record

After a success in link mode, the selected record can remain visible until the user presses Prev or Next. At that point the unlinked subset is recalculated and the linked record is no longer reachable; returning backward does not show it. If no unlinked records remain, link mode shows the empty state.

In re-link mode, the record remains in the linked subset after success, so normal Prev/Next navigation can still return to it.

Alternative considered: immediately remove the record from link mode on success. Rejected because the requested behavior says the record disappears after navigating away and then back, not necessarily instantly.

### 5. Reuse existing placeholder/action patterns

Empty states use the same cover-placeholder pattern as standby not-found. Link mode text is `No unlinked records`; re-link mode text is `No linked records`. Empty states use the fallback action bar with only Mode, matching the existing no-record pattern.

## Risks / Trade-offs

- [Race between UI fetch and event broadcast] → Update persistence before broadcasting `link_success`, and update the UI in-memory record on event receipt.
- [Event success for unknown records] → Return an error from `/events` and avoid broadcasting success when the DB update affects no row.
- [Existing `/records/<id>/link` endpoint overlaps with event success] → Keep or route it through the same database helper for compatibility, but the boardless workflow should use `link_success`.
- [No tag UID is stored] → Acceptable for boardless mode; future hardware integration can extend the payload/schema when physical tag identity is needed.

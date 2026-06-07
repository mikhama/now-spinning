## Why

Link and re-link modes currently need a complete boardless workflow for moving records between linked states after a user presses Link and an NFC/tag result arrives. The UI should guide the user through only the relevant records for each mode and make terminal-emulated NFC outcomes possible while hardware integration is still out of scope.

## What Changes

- Link mode shows only records where `linked` is false.
- Re-link mode shows only records where `linked` is true.
- Pressing the Link button starts a pending NFC/tag write state for the selected record and shows the same blinking dot indicator used by sync mode under the linked status label.
- Boardless event injection supports link success and link error outcomes through curl-posted events.
- On link success in link mode, the selected record becomes linked and is removed from the link-mode navigation set once the user navigates away; going back no longer shows it.
- On link success in re-link mode, the selected record remains visible because it is still linked.
- Link mode can be used repeatedly until no unlinked records remain, then shows an empty state with `No unlinked records`.
- Re-link mode shows an empty state with `No linked records` when there are no linked records.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `link-mode-view`: Update link and re-link record filtering, pending link visual state, success/error handling, navigation behavior, and empty-state text.
- `boardless-events`: Define curl-emulatable link success and link error events for boardless NFC/tag workflow testing.
- `api-server`: Persist linked state changes when boardless link success events are received.
- `sync-database`: Provide database support for updating a record's linked flag by record ID.

## Impact

- Frontend state and rendering for link/re-link modes, including action button handling, status indicator reuse, navigation after success, and empty states.
- WebSocket event handling for new boardless link result events.
- API server event endpoint handling for link result events and database linked-state updates.
- SQLite record persistence helper(s) for setting `linked = true`.
- Tests or manual verification with curl-posted boardless events.

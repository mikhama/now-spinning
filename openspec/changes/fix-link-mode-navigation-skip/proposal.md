## Why

After a link succeeds, the linked record remains visible until the user navigates, but it has already been removed from the filtered unlinked-record list. The current Next handler increments the old index after that list shrinks, causing the immediately following record to be skipped.

## What Changes

- Make the first Next action after a successful link show the immediately following remaining unlinked record instead of skipping it.
- Keep Prev navigation symmetric so it shows the immediately preceding remaining unlinked record.
- Preserve wrap-around behavior and the empty state when no unlinked records remain.
- Add deterministic regression coverage for navigation after a successful link.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `link-mode-view`: Clarify the required adjacent-record behavior when navigating away from a successfully linked record that is temporarily retained on screen.

## Impact

- Frontend link-mode selection and navigation logic in `ui/app.js`.
- Frontend regression tests for link-mode navigation state transitions.
- No API, persistence, or dependency changes.

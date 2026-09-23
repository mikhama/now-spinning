## Context

Link mode indexes into a list derived from `state.records` by filtering out linked records. After a successful link, the selected record is marked linked but temporarily remains visible through `retainedLinkRecordId`. Its `linkRecordIndex` is left unchanged. When Next is pressed, the retained record is cleared, the filtered list shrinks, and the existing handler increments the unchanged index. The successor has already shifted into that index, so incrementing skips it.

The fix must preserve normal navigation, wrap-around, temporary post-success retention, and the no-unlinked-records state. Re-link mode uses a stable linked-record subset and is not affected.

## Goals / Non-Goals

**Goals:**

- Make the first Next action after link success select the adjacent following unlinked record.
- Make the first Prev action after link success select the adjacent preceding unlinked record.
- Render the empty state when navigation dismisses the final retained linked record.
- Cover normal, post-success, wrap-around, and empty-list navigation deterministically.

**Non-Goals:**

- Changing NFC write or link-success event handling.
- Changing re-link navigation.
- Changing record ordering or persistence.

## Decisions

### Treat navigation away from a retained linked record as a distinct transition

When Next dismisses `retainedLinkRecordId`, it will keep the numeric `linkRecordIndex` rather than incrementing it. Removing the retained record shifts its successor into that same slot; modulo normalization handles wrap-around when the linked record was last. Prev will continue to decrement because the predecessor remains one slot before the removed record.

For navigation without a retained linked record, both handlers keep their existing increment/decrement behavior.

Alternative considered: search the full record list by ID on every navigation. That would work, but adds a second ordering algorithm when the existing filtered-list index already encodes the correct position.

### Render after dismissing the final retained record

Both navigation handlers will render even when the recalculated unlinked list is empty. This allows the existing render path to replace the retained record with the established empty state.

Alternative considered: leave the early return unchanged and rely on another event to render. Rejected because one navigation action must complete the visible transition.

### Exercise browser logic with a lightweight Node test

A Node test will evaluate `ui/app.js` in a minimal browser-like VM context, replace rendering with a spy, and drive the actual state and navigation functions. This provides behavioral regression coverage without adding a frontend package manager or application dependency.

Alternative considered: assert source-code fragments from Python tests. Rejected because textual checks cannot prove which record navigation selects.

## Risks / Trade-offs

- [The special transition depends on `retainedLinkRecordId` accurately identifying post-success display] → Existing link-success and mode-change paths already set and clear this state; tests will drive the same state transition.
- [Index boundary errors after the filtered list shrinks] → Cover middle-record navigation, last-record wrap-around, and the final-record empty state.
- [A standalone Node test might be missed by Python-only test runs] → Keep it dependency-free and run it explicitly alongside the Python suite during verification.

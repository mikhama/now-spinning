## Why

After a fresh app load, the UI currently shows a concrete record in standby before any scan has happened, and the side label can render as undefined. That leaks stale or placeholder record state into the default experience and makes the first-screen behavior inconsistent with the NFC-driven workflow.

## What Changes

- Change initial app state so a fresh load renders the standby record-not-found screen until a scan event provides a valid record.
- Restrict standby and play record rendering to records established by scan or explicit event state, instead of showing a record by default on first load.
- Define the initial displayed side for a loaded record as Side A so the side control never renders an undefined label.
- Preserve existing standby error behavior for null and unknown scan results while making the pre-scan state visually match the not-found standby screen.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `mode-state-machine`: change initial mode state and scan transition rules so the app starts in standby-not-found and only shows a record after a valid scan.
- `ui-app`: change standby/play rendering defaults so pre-scan startup shows the not-found placeholder and newly loaded records default to Side A.

## Impact

- Affected code: `ui/app.js`, standby/play rendering helpers, and any initialization logic that seeds current record or side state.
- Affected behavior: first-load UI, scan-driven record transitions, and side-label rendering.
- No new dependencies or external APIs.
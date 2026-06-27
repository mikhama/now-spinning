## Why

Kiosk mode currently has no touchscreen-accessible way to exit the app, so a user at the Raspberry Pi display needs keyboard, SSH, or process management access to stop it. A small hidden exit control in the top bar gives the operator an intentional local escape hatch without changing the visible kiosk UI.

## What Changes

- Add an invisible touch target in the top bar between the mode label and stylus info.
- Show a simple browser confirmation dialog before exiting kiosk mode.
- Add a local API action that requests kiosk shutdown only when kiosk shutdown is explicitly enabled.
- Update the kiosk runner so a shutdown request terminates the runner and cleans up the app and Chromium processes.
- Keep normal development mode protected from accidental process termination.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui-app`: Add the hidden top-bar exit control and confirmation behavior.
- `api-server`: Add a gated local shutdown endpoint for kiosk exit requests.
- `kiosk-runner`: Extend kiosk process cleanup so a UI-triggered exit stops both the app server and Chromium.

## Impact

- Affected files: `ui/index.html`, `ui/style.css`, `ui/app.js`, `api/main.py`, `bin/run_kiosk.sh`.
- Affected APIs: adds a local `POST` endpoint for kiosk exit requests.
- Affected systems: kiosk-mode process lifecycle on Raspberry Pi/Chromium.
- No new external dependencies expected.

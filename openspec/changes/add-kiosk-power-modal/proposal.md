## Why

The hidden kiosk control currently offers only browser-native Exit confirmation, and the shutdown endpoint is a placeholder. A vintage-styled dialog contained within the app screen will let touchscreen and keyboard users exit the app or request an orderly Raspberry Pi shutdown.

## What Changes

- Replace confirmation with a native HTML dialog contained in the app screen, showing the centered question `Are you sure you want to exit?` and Cancel, Exit, Shutdown buttons. Preserve the invisible trigger, vintage fonts, square corners, and rem sizing; use paper with red text for Exit and no added focus border or underline.
- Contain focus, support touch/keyboard and safe dismissal, and suspend the playback screensaver until a fresh inactivity period after dismissal.
- Preserve Exit and implement guarded systemd poweroff after persisting pending stylus hours; return JSON errors when disabled or unsuccessful.
- Close immediately on either action without showing preview/progress/success text, prevent duplicate submissions, retain failure/unconfirmed diagnostics without retry, and provide safe boardless simulations at `/#power-options`.
- Document Pi permissions and verify headed browser previews at boardless and 800×480 scales with Node, Python, and browser checks without running destructive commands.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui-app`: Replace hidden kiosk exit confirmation with accessible power options, quiet action dismissal, and boardless previews.
- `ui-design-system`: Define a compact vintage power dialog and three distinct button treatments.
- `playback-idle-screensaver`: Suspend activation during power options and restart inactivity after dismissal.
- `api-server`: Implement guarded shutdown and boardless rejection for Exit, preserving persistence and JSON responses.

## Impact

Changes affect `ui/index.html`, `ui/style.css`, `ui/app.js`, `api/main.py`, targeted Node/Python tests, and `README.md`. Raspberry Pi OS must provide systemd and passwordless permission for the kiosk user to run `/usr/bin/systemctl poweroff` through `sudo -n`. No frontend dependencies are added. The change remains active with delta specs unsynced and unarchived; actual Pi poweroff is a hardware acceptance check.

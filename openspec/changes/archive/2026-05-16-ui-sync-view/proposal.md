## Why

The app needs a dedicated view for collection synchronization — downloading updates from a remote source. Currently there's no UI for this process. The sync view gives users visual feedback during the sync operation with step-by-step status messages.

## What Changes

- Add a new "sync" mode/view accessible via `#sync` hash route
- The view reuses the stylus mode frame layout (bordered box) but displays a centered status line instead of stylus info
- Top-left label shows "Sync"
- Footer has a single "Sync" button (no prev/next navigation)
- Status line shows sync progress, initially: "Step 1/3. Downloading collection updates..."

## Capabilities

### New Capabilities
- `sync-view`: UI view for collection sync with status display, sync button, and step-based progress text

### Modified Capabilities
- `ui-app`: Adding sync as a new mode to the existing mode system (routing, render switch, action group)

## Impact

- `ui/index.html` — new mode section and action group
- `ui/app.js` — new mode in MODES array, render function, hash routing support
- `ui/style.css` — sync-specific styles (status text centering)

## Why

During playback, the current Play view remains static and small on the turntable display. After a period without touch, a full-screen now-playing view will make the song and artist readable from a distance while keeping the normal controls one touch away.

## What Changes

- Show a full-screen screensaver after Play has been active for 10 seconds and the display has received no touch for 10 seconds.
- Dismiss it on touch and start a new 10-second inactivity period; leave it hidden outside Play.
- Derive the background automatically from the cover's strongest colorful hue family, using a bright representative of that family. Fall back to the existing RGB bucket result for covers without a substantial colorful region, and choose black or white text by contrast. Do not use record-specific colors.
- Display the current track's artist when provided, otherwise the record artist, with the song on a separate, larger upright line. Scroll either line when its text exceeds the available width.
- Show elapsed playback time in the upper-right corner, with corner typography and insets matching the current status bar; remove the cover miniature and divider from the preview design.
- Remove the temporary `previews/` directory after the feature is implemented.
- Remove the temporary `examples/` color experiments after transferring the selected algorithm into the UI.

## Capabilities

### New Capabilities

- `playback-idle-screensaver`: Playback-only activation, touch dismissal, cover-derived colors, track metadata, time, and overflow behavior.

### Modified Capabilities

None.

## Impact

The change affects `ui/index.html`, `ui/style.css`, and `ui/app.js`. It uses the existing record and playback status data, same-origin cover images, and browser canvas APIs. It adds no dependency or backend API.

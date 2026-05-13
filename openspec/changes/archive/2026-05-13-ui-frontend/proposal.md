## Why

The Now Spinning system currently has a Python API but no user-facing interface. The Raspberry Pi with an 800×480 (4.3") display needs a lightweight UI so users can interact with records and styli without requiring a separate device. The API already serves data and WebSocket events — a frontend completes the user experience.

## What Changes

- Add a static HTML/CSS/JS frontend served by the Flask API (no frameworks, no build step)
- Three files: `ui/index.html`, `ui/style.css`, `ui/app.js`
- Fixed 800×480 layout targeting the Raspberry Pi 4.3" display — no responsiveness, large text for readability
- Implement all application modes: **Standby**, **Play**, **Link**, **Re-Link**, and **Stylus**
- Connect to REST endpoints (`/records`, `/styli`, `/records/<id>/link`, `/styli/<id>/reset`) and the `/ws` WebSocket for live updates (current record, stylus hours, temperature, playback status)
- Display cover art, album/artist info, track listing, catalogue number, link status, stylus name, and stylus distance/hours
- Show contextual actions per mode: navigate records/styli, prev/next song, side switching
- Handle error/empty states:
  - Standby: "NFC Reading Error" (cover placeholder) and "Record Not Found" (cover placeholder)
  - Link: "Link Error" tag
  - Stylus: "No styli found!"
- Mode button and Link/Reset actions are present but disabled (future implementation)
- Dev mode via URL hash to quickly preview any mode/state combination:
  - `#standby` — Standby with current record
  - `#standby-error` — NFC Reading Error with cover placeholder
  - `#standby-not-found` — Record Not Found with cover placeholder
  - `#play` — Play mode with current track
  - `#link` — Link mode with current record
  - `#link-error` — Link mode with "Link Error" state
  - `#re-link` — Re-Link mode (only linked records)
  - `#stylus` — Stylus mode with current stylus
  - `#stylus-error` — Stylus mode with no styli ("No styli found!")

## Capabilities

### New Capabilities
- `ui-app`: Core frontend application — HTML structure, CSS layout (800×480 fixed), JS logic for mode management, REST calls, WebSocket connection, and screen rendering for all modes (Standby, Play, Link, Re-Link, Stylus)

### Modified Capabilities
- `api-server`: Add static file serving so Flask hosts the `ui/` directory assets

## Impact

- **Code**: New files `ui/index.html`, `ui/style.css`, `ui/app.js`; minor change to `api/main.py` to serve static files
- **APIs**: No new endpoints; frontend consumes existing REST and WebSocket APIs
- **Dependencies**: None — pure HTML/CSS/JS with no external libraries

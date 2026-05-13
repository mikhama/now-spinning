## Context

The Now Spinning system runs on a Raspberry Pi with a 4.3" 800×480 display. The Flask API (`api/main.py`) already provides REST endpoints for records/styli and a WebSocket at `/ws` that pushes live state events. There is no frontend — users currently have no way to interact with the system visually. The `ui/` directory exists with a cover image asset but no HTML/CSS/JS files.

## Goals / Non-Goals

**Goals:**
- Serve a static frontend from Flask without adding dependencies
- Fixed 800×480 pixel layout — no scrolling, no responsiveness
- Large, readable text optimized for a 4.3" display
- Implement all modes: Standby, Play, Link, Re-Link, Stylus
- Connect to existing REST and WebSocket APIs for live data
- Handle error states: NFC Reading Error, Record Not Found, Link Error, No styli found

**Non-Goals:**
- Mobile or desktop responsive design
- CSS frameworks, JS frameworks, or build tooling
- Offline support or service workers
- Authentication or access control
- Creating new API endpoints
- Implementing Mode button switching (future)
- Implementing Link/Re-Link/Reset actions (future)

## Decisions

### 1. Static file serving via Flask's `static_folder`

Configure `Flask(static_folder="../ui", static_url_path="/")` and add a catch-all route to serve `index.html`. This avoids adding a reverse proxy or extra dependencies.

**Alternative considered**: Using `send_from_directory` with explicit routes — rejected because a single `static_folder` config is simpler and handles CSS/JS/images automatically.

### 2. Single HTML page with JS-driven mode switching

One `index.html` page with sections for each mode, toggled via CSS `display` property from JS. No client-side routing.

URL hash fragments are used as a dev mode to jump directly to any mode or error state for quick preview. The `hashchange` event re-fetches data and applies the requested state. Supported hashes:

| Hash | Mode | State |
|------|------|-------|
| `#standby` | Standby | Normal — shows current record |
| `#standby-error` | Standby | NFC Reading Error — cover placeholder with error text |
| `#standby-not-found` | Standby | Record Not Found — cover placeholder with message |
| `#play` | Play | Normal — shows current track |
| `#link` | Link | Normal — shows current record link status |
| `#link-error` | Link | Error — shows "Link Error" tag |
| `#re-link` | Re-Link | Shows only linked records |
| `#stylus` | Stylus | Normal — shows current stylus info |
| `#stylus-error` | Stylus | Empty — clears styli list, shows "No styli found!" |

Error variants work by manipulating app state before rendering: `standby-error` sets `standbyError = "nfc"`, `standby-not-found` sets `standbyError = "not-found"`, `link-error` sets the link error flag, `stylus-error` empties the styli array, `re-link` marks all records as linked. On hash change, data is re-fetched first to reset any previous overrides.

When a URL hash is present, WebSocket status events (playing/idle) are ignored to prevent dev mode from being overridden.

**Alternative considered**: Multiple HTML pages per mode — rejected because mode transitions need to preserve WebSocket state and in-memory data without page reloads.

### 3. File structure: `ui/index.html`, `ui/style.css`, `ui/app.js`

Three files as requested. CSS handles the fixed 800×480 layout. JS handles all API calls, WebSocket connection, state management, and DOM updates.

### 4. Five modes: Standby, Play, Link, Re-Link, Stylus

- **Standby**: Shows current record (cover, ID, artist, title) or error states (NFC error / not found with cover placeholders)
- **Play**: Shows current record + currently playing track with side label
- **Link**: Shows all records with linked/not-linked status, Prev/Next navigation
- **Re-Link**: Shows only linked records with Prev/Next navigation (separate index from Link)
- **Stylus**: Shows stylus name and distance/hours

Mode button is present in Standby, Link, Re-Link, and Stylus action bars but is currently disabled (no click handler). Mode switching is only possible via URL hash for now.

### 5. Split-grid layout for record display

All modes that show record info use a 1:1 horizontal split-grid: cover image on the left, text info on the right. This provides a symmetrical, balanced layout on the 800×480 display.

### 6. Side button in Standby and Play

Both Standby and Play modes have a "Side" button that shows the current side label (e.g., "Side A") and cycles through sides when clicked. In Play mode, switching sides also resets the track index.

### 7. Button styling for 4.3" touchscreen

Buttons have no border-radius, no spacing between them, and fill their entire grid cell. Font size is 18px for readability on the small display. The action bar uses a 4-column grid where unused slots are invisible placeholders.

### 8. Text hierarchy for readability

Font sizes are differentiated for a clear visual hierarchy on the 4.3" display:
- Record ID: 16px (gray, secondary)
- Artist: 26px (semibold)
- Album title: 32px (bold, largest)
- Now playing track: 22px (blue accent)

### 9. Error/status tags in gray

Link status ("Linked", "Not Linked") and error ("Link Error") tags use gray text with a gray border, no background color, no border-radius. This keeps the UI neutral and consistent.

### 10. Cover placeholder for error states

Standby error states (NFC Reading Error, Record Not Found) show a gray cover placeholder box with the error message text centered inside it, instead of displaying text in the info column.

### 11. WebSocket reconnect with simple retry

On disconnect, retry connection every 3 seconds. No exponential backoff — this is a local network appliance with a single client.

### 12. Cover images served from `ui/images/`

The `cover_image` field in record data already points to `ui/images/<release_id>.jpeg`. Since Flask serves the `ui/` directory as static root, images are accessible at `/images/<release_id>.jpeg`.

## Risks / Trade-offs

- **[Single client assumption]** → The UI assumes one display. Multiple browser clients connecting to the same WebSocket will receive the same events but could desynchronize mode state. Mitigation: acceptable for a dedicated Raspberry Pi kiosk.
- **[No caching strategy]** → Static files have no cache headers. Mitigation: local network, single client — performance is not a concern.
- **[Mock data only]** → The API currently returns hardcoded mock data. The UI will work correctly with it now and with real data later when the backend is connected to NFC/Discogs. No migration needed.
- **[Disabled actions]** → Mode, Link, Re-Link, and Reset buttons are rendered but non-functional. This is intentional — the backend logic will be wired up in a future change.

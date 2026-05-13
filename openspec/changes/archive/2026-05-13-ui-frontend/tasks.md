## 1. API Static File Serving

- [x] 1.1 Update `api/main.py` to configure Flask with `static_folder` pointing to `../ui` and `static_url_path=""`
- [x] 1.2 Add a catch-all route to serve `ui/index.html` at `/`

## 2. HTML Structure

- [x] 2.1 Create `ui/index.html` with the base document, viewport meta, CSS/JS links
- [x] 2.2 Add top bar markup: mode label (left), stylus hours (right)
- [x] 2.3 Add main content area with sections for each mode (Standby, Play, Link, Re-Link, Stylus) — each hidden by default
- [x] 2.4 Add Standby error states: NFC Reading Error and Record Not Found with cover placeholders
- [x] 2.5 Add Link/Re-Link error state markup: "Link Error" tag
- [x] 2.6 Add Stylus empty state: "No styli found!"
- [x] 2.7 Add bottom action bar markup with mode-specific button groups (Standby, Play, Link, Re-Link, Stylus)

## 3. CSS Layout

- [x] 3.1 Create `ui/style.css` with 800×480 fixed viewport, no scrolling, base reset
- [x] 3.2 Style the top bar (mode label left, stylus hours right)
- [x] 3.3 Style split-grid layout (1:1 columns) for record display modes
- [x] 3.4 Style cover images and cover placeholder (gray background, border, centered text)
- [x] 3.5 Style text hierarchy: record-id 16px, artist 26px, title 32px, now-playing 22px
- [x] 3.6 Style link/error status tags (gray text, gray border, no border-radius)
- [x] 3.7 Style the bottom action bar: buttons fill cells, no gap, no border-radius, 18px font
- [x] 3.8 Style empty/error states

## 4. JavaScript — Core State & Mode Management

- [x] 4.1 Create `ui/app.js` with app state object (current mode, records list, styli list, current record ID, link/re-link record indices, current stylus index, current track/side, standbyError, linkError)
- [x] 4.2 Implement five modes: standby, play, link, re-link, stylus
- [x] 4.3 Implement render functions that show/hide mode sections and update DOM elements based on current state
- [x] 4.4 Mode button present but disabled (no switching logic wired)

## 5. JavaScript — REST API Integration

- [x] 5.1 Implement `GET /records` fetch on page load, populate records list
- [x] 5.2 Implement `GET /styli` fetch on page load, populate styli list
- [x] 5.3 Implement `POST /records/<id>/link` call (present but button disabled)
- [x] 5.4 Implement `POST /styli/<id>/reset` call (present but button disabled)

## 6. JavaScript — WebSocket Integration

- [x] 6.1 Establish WebSocket connection to `/ws` on page load
- [x] 6.2 Handle `current_record` event — update current record display
- [x] 6.3 Handle `stylus_hours` event — update stylus hours in top bar and Stylus mode
- [x] 6.4 Handle `status` event — auto-transition between Standby and Play modes (disabled when URL hash is present)
- [x] 6.5 Handle `temperature_c` event — store in state
- [x] 6.6 Implement reconnect logic (retry every 3 seconds on disconnect)

## 7. JavaScript — Mode-Specific Rendering

- [x] 7.1 Standby mode: show current record (cover, ID, artist, title) or error states (NFC error / not found with cover placeholder)
- [x] 7.2 Play mode: show current record + current track, side label
- [x] 7.3 Link mode: show all records with Linked/Not Linked status or Link Error
- [x] 7.4 Re-Link mode: show only linked records with Linked status
- [x] 7.5 Stylus mode: show stylus name and distance/hours or "No styli found!"

## 8. JavaScript — Mode-Specific Interactions

- [x] 8.1 Standby: Side button to switch sides
- [x] 8.2 Play: Prev/Next song navigation, side switching
- [x] 8.3 Link: Prev/Next record navigation
- [x] 8.4 Re-Link: Prev/Next linked record navigation (separate index)
- [x] 8.5 Stylus: Prev/Next stylus navigation

## 9. JavaScript — Dev Mode (URL Hash)

- [x] 9.1 Parse URL hash on load and on `hashchange`
- [x] 9.2 Support `#standby`, `#play`, `#link`, `#re-link`, `#stylus` for normal modes
- [x] 9.3 Support `#standby-error` (NFC Reading Error)
- [x] 9.4 Support `#standby-not-found` (Record Not Found)
- [x] 9.5 Support `#link-error` (Link Error state)
- [x] 9.6 Support `#stylus-error` (empty styli list)
- [x] 9.7 Support `#re-link` (marks all records as linked for demo)
- [x] 9.8 Re-fetch data on hash change to reset previous overrides
- [x] 9.9 Ignore WebSocket status events when hash is present

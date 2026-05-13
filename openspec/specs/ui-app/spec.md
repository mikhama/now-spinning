# ui-app Specification

## Purpose
Frontend UI application for the Now Spinning turntable controller, rendered at 800×480 on a Raspberry Pi touchscreen display.

## Requirements

### Requirement: Fixed 800×480 viewport layout
The UI SHALL render at exactly 800×480 pixels with no scrolling and no responsive breakpoints.

#### Scenario: Page loads on Raspberry Pi display
- **WHEN** the page loads in an 800×480 viewport
- **THEN** the entire UI SHALL be visible without horizontal or vertical scrolling

### Requirement: Three-file frontend structure
The frontend SHALL consist of exactly three files: `ui/index.html`, `ui/style.css`, and `ui/app.js` with no external dependencies or frameworks.

#### Scenario: Files exist
- **WHEN** the `ui/` directory is listed
- **THEN** it SHALL contain `index.html`, `style.css`, and `app.js`

### Requirement: Persistent top bar
The UI SHALL display a persistent top bar across all modes showing the current mode label on the left and stylus hours on the right.

#### Scenario: Top bar displays mode label
- **WHEN** the current mode is "Standby"
- **THEN** the top bar SHALL show "Standby" on the left side

#### Scenario: Top bar displays stylus hours
- **WHEN** a stylus is loaded with 89.6 hours
- **THEN** the top bar SHALL show "89.6 h" on the right

### Requirement: Five application modes
The UI SHALL support five modes: Standby, Play, Link, Re-Link, and Stylus. Mode switching via the Mode button is disabled — modes are only reachable via URL hash in dev mode or via WebSocket events (play/idle status).

#### Scenario: Modes exist
- **WHEN** the UI is initialized
- **THEN** the mode list SHALL contain "standby", "play", "link", "re-link", and "stylus"

### Requirement: Split-grid layout
All modes displaying record information SHALL use a 1:1 horizontal split-grid layout with cover image on the left column and text information on the right column.

#### Scenario: Record displayed in split-grid
- **WHEN** a record is shown in Standby, Play, Link, or Re-Link mode
- **THEN** the cover image SHALL appear in the left half and text info in the right half

### Requirement: Text hierarchy for 4.3" display readability
Text SHALL use differentiated sizes for visual hierarchy: record ID (16px), artist (26px), album title (32px), now-playing track (22px).

#### Scenario: Text sizes render correctly
- **WHEN** a record is displayed
- **THEN** the album title SHALL be the largest text, followed by artist, then track name, then record ID

### Requirement: Standby mode — record display
In Standby mode, the UI SHALL display the current record's cover image, catalogue number (#ID), artist, and title. A Side button SHALL show the current side label and allow switching sides.

#### Scenario: Record is available in Standby
- **WHEN** the mode is Standby and a record is loaded
- **THEN** the UI SHALL show the cover image, "#<id>", artist name, album title, and a Side button

#### Scenario: Side button in Standby
- **WHEN** the user clicks the Side button in Standby
- **THEN** the UI SHALL cycle to the next side and update the button label

### Requirement: Standby mode — NFC Reading Error
In Standby mode, when an NFC reading error occurs, the UI SHALL display a gray cover placeholder with "NFC Reading Error" text centered inside it.

#### Scenario: NFC reading error in Standby
- **WHEN** the mode is Standby and an NFC reading error occurs
- **THEN** the UI SHALL show a cover placeholder with "NFC Reading Error" text inside

### Requirement: Standby mode — Record Not Found
In Standby mode, when a scanned record is not found in the database, the UI SHALL display a gray cover placeholder with "Record Not Found" text centered inside it.

#### Scenario: Record not found in Standby
- **WHEN** the mode is Standby and the scanned record is not in the database
- **THEN** the UI SHALL show a cover placeholder with "Record Not Found" text inside

### Requirement: Cover placeholder
Error states that would normally show a cover image SHALL instead display a gray placeholder box (280×280px, gray background, gray border) with descriptive text centered inside.

#### Scenario: Cover placeholder renders
- **WHEN** an error state requires a cover placeholder
- **THEN** the placeholder SHALL be a gray box with centered gray text describing the error

### Requirement: Play mode — now playing display
In Play mode, the UI SHALL display the current record's cover image, catalogue number, artist, title, currently playing track name (blue accent), current side label, and prev/next song navigation.

#### Scenario: Track is playing
- **WHEN** the mode is Play and a record with tracks is loaded
- **THEN** the UI SHALL show the cover image, "#<id>", artist, title, track name, side label, and "<Prev" / "Next>" buttons

#### Scenario: Side switching in Play
- **WHEN** the user clicks the Side button in Play mode
- **THEN** the UI SHALL cycle to the next side and reset the track index to 0

### Requirement: Link mode — record browsing
In Link mode, the UI SHALL display all records (linked and not linked) with cover image, catalogue number, artist, title, and link status tag. Prev/Next buttons navigate through all records.

#### Scenario: Record is not linked
- **WHEN** the mode is Link and the current record has `linked: false`
- **THEN** the UI SHALL show a "Not Linked" status tag

#### Scenario: Record is linked
- **WHEN** the mode is Link and the current record has `linked: true`
- **THEN** the UI SHALL show a "Linked" status tag

#### Scenario: Link error
- **WHEN** the link error flag is set
- **THEN** the UI SHALL show a "Link Error" tag instead of the status tag

#### Scenario: Navigate records in Link mode
- **WHEN** the user clicks "<Prev" or "Next>" in Link mode
- **THEN** the UI SHALL navigate to the previous or next record in the full list

### Requirement: Re-Link mode — linked records only
In Re-Link mode, the UI SHALL display only records that have `linked: true`. It SHALL have its own navigation index separate from Link mode.

#### Scenario: Re-Link shows linked records
- **WHEN** the mode is Re-Link
- **THEN** only records with `linked: true` SHALL be shown

#### Scenario: Navigate records in Re-Link mode
- **WHEN** the user clicks "<Prev" or "Next>" in Re-Link mode
- **THEN** the UI SHALL navigate through linked records only

### Requirement: Link/error status tag styling
Link status tags ("Linked", "Not Linked") and error tags ("Link Error") SHALL use gray text with a gray border, no background color, and no border-radius.

#### Scenario: Status tag appearance
- **WHEN** a link status or error tag is displayed
- **THEN** it SHALL have gray text, a gray border, and no rounded corners

### Requirement: Stylus mode — stylus info display
In Stylus mode, the UI SHALL display the current stylus name and distance/hours, with Prev/Next navigation.

#### Scenario: Stylus is available
- **WHEN** the mode is Stylus and a stylus is loaded
- **THEN** the UI SHALL show the stylus name and "Distance: <hours> h"

#### Scenario: No styli found
- **WHEN** the mode is Stylus and no styli are available
- **THEN** the UI SHALL show "No styli found!" message

### Requirement: Button styling for touchscreen
Action bar buttons SHALL have no border-radius, no spacing between them, fill their entire grid cell (width and height 100%), and use 18px font size for readability on the 4.3" display.

#### Scenario: Button fills cell
- **WHEN** an action button is rendered
- **THEN** it SHALL fill the full width and height of its grid cell with no gaps between adjacent buttons

### Requirement: Disabled action buttons
The Mode button, Link button, Re-Link button, and Reset Stylus button SHALL be rendered but have no click handlers attached (future implementation).

#### Scenario: Mode button does nothing
- **WHEN** the user clicks the Mode button
- **THEN** nothing SHALL happen — no mode change

#### Scenario: Link button does nothing
- **WHEN** the user clicks the Link or Re-Link button
- **THEN** nothing SHALL happen — no API call

#### Scenario: Reset button does nothing
- **WHEN** the user clicks the Reset button in Stylus mode
- **THEN** nothing SHALL happen — no API call

### Requirement: REST API integration
The UI SHALL fetch data from the API's REST endpoints on load.

#### Scenario: Initial data load
- **WHEN** the page loads
- **THEN** the UI SHALL fetch `GET /records` and `GET /styli` to populate local state

### Requirement: WebSocket connection for live updates
The UI SHALL establish a WebSocket connection to `/ws` and process incoming events to update the display in real time. WebSocket status events SHALL be ignored when a URL hash is present (dev mode).

#### Scenario: Receive stylus_hours event
- **WHEN** the WebSocket sends `{"event": "stylus_hours", "data": {"hours": 89.6, "stylus_id": "1"}}`
- **THEN** the UI SHALL update the stylus hours display

#### Scenario: Receive current_record event
- **WHEN** the WebSocket sends `{"event": "current_record", "data": {"record_id": "1"}}`
- **THEN** the UI SHALL update the current record display

#### Scenario: Receive status event (no hash)
- **WHEN** the WebSocket sends `{"event": "status", "data": {"status": "playing"}}` and no URL hash is present
- **THEN** the UI SHALL transition to Play mode if currently in Standby

#### Scenario: Receive status event (with hash)
- **WHEN** the WebSocket sends a status event and a URL hash is present
- **THEN** the UI SHALL ignore the event and NOT change modes

#### Scenario: WebSocket reconnect on disconnect
- **WHEN** the WebSocket connection is lost
- **THEN** the UI SHALL attempt to reconnect every 3 seconds

### Requirement: Bottom action bar
The UI SHALL display a bottom action bar with mode-specific buttons in a 4-column grid. Unused slots SHALL be invisible placeholders.

#### Scenario: Standby mode actions
- **WHEN** the mode is Standby
- **THEN** the bottom bar SHALL show: [placeholder], Mode, Side, [placeholder]

#### Scenario: Play mode actions
- **WHEN** the mode is Play
- **THEN** the bottom bar SHALL show: <Prev, [placeholder], Side, Next>

#### Scenario: Link mode actions
- **WHEN** the mode is Link
- **THEN** the bottom bar SHALL show: <Prev, Mode, Link, Next>

#### Scenario: Re-Link mode actions
- **WHEN** the mode is Re-Link
- **THEN** the bottom bar SHALL show: <Prev, Mode, Re-Link, Next>

#### Scenario: Stylus mode actions
- **WHEN** the mode is Stylus
- **THEN** the bottom bar SHALL show: <Prev, Mode, Reset, Next>

### Requirement: Dev mode via URL hash
The UI SHALL support URL hash fragments to switch to any mode or error state for development and preview purposes. On page load and on `hashchange`, the UI SHALL parse the hash, re-fetch data from the API, and apply the requested state.

#### Scenario: Navigate to normal mode via hash
- **WHEN** the URL hash is set to `#standby`, `#play`, `#link`, `#re-link`, or `#stylus`
- **THEN** the UI SHALL switch to the corresponding mode with normal data

#### Scenario: Navigate to Standby NFC error via hash
- **WHEN** the URL hash is set to `#standby-error`
- **THEN** the UI SHALL switch to Standby mode showing the NFC Reading Error cover placeholder

#### Scenario: Navigate to Standby not-found via hash
- **WHEN** the URL hash is set to `#standby-not-found`
- **THEN** the UI SHALL switch to Standby mode showing the Record Not Found cover placeholder

#### Scenario: Navigate to Link error via hash
- **WHEN** the URL hash is set to `#link-error`
- **THEN** the UI SHALL switch to Link mode with the error flag set, showing "Link Error" tag

#### Scenario: Navigate to Re-Link via hash
- **WHEN** the URL hash is set to `#re-link`
- **THEN** the UI SHALL switch to Re-Link mode with all records marked as linked (for demo purposes)

#### Scenario: Navigate to Stylus error via hash
- **WHEN** the URL hash is set to `#stylus-error`
- **THEN** the UI SHALL switch to Stylus mode with an empty styli list, showing "No styli found!"

#### Scenario: Hash change resets previous overrides
- **WHEN** the URL hash changes from an error hash to a normal hash
- **THEN** the UI SHALL re-fetch records and styli from the API before applying the new state, restoring normal data

#### Scenario: Invalid or empty hash
- **WHEN** the URL hash is empty or contains an unrecognized mode name
- **THEN** the UI SHALL ignore the hash and render normally

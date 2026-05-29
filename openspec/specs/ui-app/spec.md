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
The UI SHALL display a persistent top bar across all modes with `background: var(--paper)`, `border-bottom: 2px solid var(--ink)`, showing the current mode label in DM Mono 11px uppercase on the left. In Play mode, when runtime state includes a playback time derived from a server `status` event, the left side SHALL render `PLAY {mm:ss}` with a single space separator. When no playback time is available, the left side SHALL render only the mode label. The right side SHALL contain a compact stylus wear bar (≈4rem × 0.5rem) followed by the Pi temperature in DM Mono 11px `color: var(--ink-mute)` format "{int} °C". The previous plain-text stylus hours display is removed from the top bar.

#### Scenario: Top bar displays mode label
- **WHEN** the current mode is "Standby"
- **THEN** the top bar SHALL show "STANDBY" in DM Mono uppercase on the left side with ink-colored text

#### Scenario: Top bar displays play time
- **WHEN** the current mode is "Play" and the current playback time is `00:01`
- **THEN** the top bar SHALL show `PLAY 00:01` on the left side

#### Scenario: Top bar omits play time when unavailable
- **WHEN** the current mode is "Play" and no playback time is available in runtime state
- **THEN** the top bar SHALL show `PLAY` with no trailing placeholder time

#### Scenario: Top bar displays compact stylus bar
- **WHEN** a stylus is loaded with 600 hours (capacity_max 1000)
- **THEN** the top bar right side SHALL show a compact progress bar filled to 60%

#### Scenario: Top bar hides compact bar when no styli
- **WHEN** no styli are loaded
- **THEN** the top bar SHALL hide the compact stylus bar entirely

#### Scenario: Top bar displays Pi temperature
- **WHEN** the Pi temperature is 59°C
- **THEN** the top bar right side SHALL show "59 °C" after the stylus bar, in DM Mono ink-mute color

### Requirement: Five application modes
The UI SHALL support six modes: Standby, Play, Link, Re-Link, Stylus, and Sync. Mode switching via the Mode button SHALL cycle through: standby → sync → link → re-link → stylus → standby. Play mode SHALL only be reachable via WebSocket `status` events. Hash-based dev routing SHALL remain functional.

#### Scenario: Modes exist
- **WHEN** the UI is initialized
- **THEN** the mode list SHALL contain "standby", "play", "link", "re-link", "stylus", and "sync"

#### Scenario: Mode button cycles defined order
- **WHEN** the mode button is pressed in standby mode
- **THEN** the mode SHALL advance to "sync", then "link", "re-link", "stylus", and back to "standby"

#### Scenario: Play mode not in button cycle
- **WHEN** the mode button is pressed
- **THEN** "play" mode SHALL never be entered via the mode button

### Requirement: Split-grid layout
All modes displaying record information SHALL use a 1:1 horizontal split-grid layout with cover image on the left column and text information on the right column.

#### Scenario: Record displayed in split-grid
- **WHEN** a record is shown in Standby, Play, Link, or Re-Link mode
- **THEN** the cover image SHALL appear in the left half and text info in the right half

### Requirement: Text hierarchy for 4.3" display readability
Text SHALL use the design system's three-font hierarchy: record ID in Gloock 2.4rem amber-deep bordered badge (top-right), artist in Gloock 3rem (ink), album title in Fraunces italic 2.2rem (amber-deep), now-playing track in Fraunces 1.8rem (ink-soft).

#### Scenario: Text sizes and fonts render correctly
- **WHEN** a record is displayed
- **THEN** the album title SHALL be in Fraunces italic amber-deep, artist in Gloock, track in Fraunces, and record ID in Gloock bordered badge

### Requirement: Record ID display format
Record IDs SHALL be displayed as zero-padded numbers (minimum 2 digits) without a hash prefix. For example, record id "1" displays as "01", record id "12" displays as "12".

#### Scenario: Single-digit record ID
- **WHEN** a record with id "1" is displayed
- **THEN** the record ID text SHALL be "01"

#### Scenario: Multi-digit record ID
- **WHEN** a record with id "42" is displayed
- **THEN** the record ID text SHALL be "42"

### Requirement: Standby mode — record display
In Standby mode, the UI SHALL display the current record's cover image, catalogue number (#ID), artist, and title only when a current record has been established by runtime state. A Side button SHALL show the current side label and allow switching sides. When a newly loaded record has sides, the initial displayed side SHALL be the first side and SHALL render as "Side A" when the first side label is "A".

#### Scenario: Record is available in Standby
- **WHEN** the mode is Standby and a valid current record has been loaded after a scan or runtime event
- **THEN** the UI SHALL show the cover image, "#<id>", artist name, album title, and a Side button

#### Scenario: Initial side label in Standby
- **WHEN** the mode is Standby and a newly loaded record has sides beginning with side id "A"
- **THEN** the Side button SHALL initially display "Side A"

#### Scenario: Side button in Standby
- **WHEN** the user clicks the Side button in Standby
- **THEN** the UI SHALL cycle to the next side and update the button label

### Requirement: Standby mode — NFC Reading Error
In Standby mode, when an NFC reading error occurs, the UI SHALL display a gray cover placeholder with "NFC Reading Error" text centered inside it.

#### Scenario: NFC reading error in Standby
- **WHEN** the mode is Standby and an NFC reading error occurs
- **THEN** the UI SHALL show a cover placeholder with "NFC Reading Error" text inside

### Requirement: Standby mode — Record Not Found
In Standby mode, when a scanned record is not found in the database, or when the app has just loaded before any record scan has succeeded, the UI SHALL display a gray cover placeholder with "Record Not Found" text centered inside it.

#### Scenario: Record not found in Standby
- **WHEN** the mode is Standby and the scanned record is not in the database
- **THEN** the UI SHALL show a cover placeholder with "Record Not Found" text inside

#### Scenario: Startup before first scan
- **WHEN** the app loads with no URL hash and no successful scan has happened yet
- **THEN** the standby view SHALL show the same "Record Not Found" placeholder instead of record metadata

### Requirement: Cover placeholder
Error states that would normally show a cover image SHALL instead display a placeholder box (280×280px) with `background: var(--paper-dark)`, `border: 1px solid var(--ink-soft)`, and descriptive text in DM Mono uppercase `color: var(--ink-mute)` centered inside.

#### Scenario: Cover placeholder renders
- **WHEN** an error state requires a cover placeholder
- **THEN** the placeholder SHALL be a paper-dark box with centered DM Mono uppercase text in ink-mute color

### Requirement: Play mode — now playing display
In Play mode, the UI SHALL display the current record's cover image, catalogue number, artist, title, a currently playing track label (blue accent), current side label, and prev/next song navigation only when a valid current record with playable side data is loaded. When the current track provides a non-empty artist that is separate from the album-level record artist, the track label SHALL render as `{song_title} ({artist})`. Otherwise, the track label SHALL render as the track title only.

#### Scenario: Track is playing
- **WHEN** the mode is Play and a record with tracks is loaded
- **THEN** the UI SHALL show the cover image, `#<id>`, artist, title, track label, side label, and `<Prev` / `Next>` buttons

#### Scenario: Track has a separate artist
- **WHEN** the mode is Play and the current track has a non-empty `artist` value that differs from the current record's `artist`
- **THEN** the track label SHALL render as `{track.title} ({track.artist})`

#### Scenario: Track uses album artist
- **WHEN** the mode is Play and the current track has no `artist` value or the track `artist` matches the current record's `artist`
- **THEN** the track label SHALL render as `{track.title}` with no artist suffix

#### Scenario: Side switching in Play
- **WHEN** the user clicks the Side button in Play mode while a valid record is loaded
- **THEN** the UI SHALL cycle to the next side and reset the track index to `0`

### Requirement: Link mode — unlinked record browsing
In Link mode, the UI SHALL display only unlinked records (where `linked` is false) with cover image, catalogue number, artist, title, and link status tag. Prev/Next buttons navigate through unlinked records only.

#### Scenario: Record is not linked
- **WHEN** the mode is Link and the current record has `linked: false`
- **THEN** the UI SHALL show a "Not Linked" status tag

#### Scenario: Link error
- **WHEN** the link error flag is set
- **THEN** the UI SHALL show a "Link Error" tag instead of the status tag

#### Scenario: Navigate records in Link mode
- **WHEN** the user clicks "<Prev" or "Next>" in Link mode
- **THEN** the UI SHALL navigate to the previous or next record in the unlinked records list, wrapping at boundaries

### Requirement: Link mode — empty state view
Link mode SHALL include an empty state grid (hidden by default) with a cover placeholder displaying "No Unlinked Records" text, using the same visual pattern as the standby "Record Not Found" placeholder.

#### Scenario: Empty state HTML structure
- **WHEN** the link mode section is rendered
- **THEN** it SHALL contain a hidden empty-state grid with a cover-placeholder and "No Unlinked Records" text

### Requirement: Link mode — renders empty state when no unlinked records
The `renderLink()` function SHALL check for unlinked records. When none exist, it SHALL hide the record grid and show the empty state grid. When unlinked records exist, it SHALL show the record grid and hide the empty state.

#### Scenario: No unlinked records available
- **WHEN** `renderLink()` is called and no unlinked records exist
- **THEN** the record grid SHALL be hidden and the empty state grid SHALL be visible

#### Scenario: Unlinked records available
- **WHEN** `renderLink()` is called and unlinked records exist
- **THEN** the record grid SHALL be visible and the empty state grid SHALL be hidden

### Requirement: Re-Link mode — linked records only
In Re-Link mode, the UI SHALL display only records that have `linked: true`. It SHALL have its own navigation index separate from Link mode.

#### Scenario: Re-Link shows linked records
- **WHEN** the mode is Re-Link
- **THEN** only records with `linked: true` SHALL be shown

#### Scenario: Navigate records in Re-Link mode
- **WHEN** the user clicks "<Prev" or "Next>" in Re-Link mode
- **THEN** the UI SHALL navigate through linked records only

### Requirement: Link/error status tag styling
Link status tags ("Linked", "Not Linked") SHALL use DM Mono uppercase, `color: var(--amber-deep)`, `border: 1px solid var(--amber-deep)`. Error tags ("Link Error") SHALL use `color: var(--red-ink)`, `border: 1px solid var(--red-ink)`. No background fill, no border-radius.

#### Scenario: Status tag appearance
- **WHEN** a link status tag is displayed
- **THEN** it SHALL have amber-deep text and border, DM Mono uppercase, no background

#### Scenario: Error tag appearance
- **WHEN** a link error tag is displayed
- **THEN** it SHALL have red-ink text and border, DM Mono uppercase, no background

### Requirement: Hide irrelevant action buttons in error/empty states
The "Side" action button SHALL be hidden (visibility: hidden) when in standby error states (NFC error, Record Not Found) and when stylus mode displays "No styli found". The button SHALL only be visible when a valid record is loaded.

#### Scenario: Side button hidden on NFC error
- **WHEN** standby mode shows NFC Reading Error
- **THEN** the Side button SHALL NOT be visible

#### Scenario: Side button hidden on not found
- **WHEN** standby mode shows Record Not Found
- **THEN** the Side button SHALL NOT be visible

#### Scenario: Side button hidden on empty stylus
- **WHEN** stylus mode shows "No styli found"
- **THEN** the Side button SHALL NOT be visible

#### Scenario: Side button visible with valid record
- **WHEN** standby mode displays a loaded record
- **THEN** the Side button SHALL be visible

### Requirement: Stylus mode — stylus info display
In Stylus mode, the UI SHALL display the current stylus name and distance/hours, with Prev/Next navigation.

#### Scenario: Stylus is available
- **WHEN** the mode is Stylus and a stylus is loaded
- **THEN** the UI SHALL show the stylus name and "Distance: <hours> h"

#### Scenario: No styli found
- **WHEN** the mode is Stylus and no styli are available
- **THEN** the UI SHALL show "No styli found!" message

### Requirement: Stylus mode — stylus display with wear bar
In Stylus mode, the UI SHALL display the stylus name, a full-size wear progress bar (≈20rem × 1rem) with capacity-aware coloring, and the hours text below it in DM Mono 1.4rem showing "{hours} h".

#### Scenario: Stylus page shows full bar and hours
- **WHEN** the mode is Stylus and a stylus has 750 hours (capacity_min 800, capacity_max 1000)
- **THEN** the page SHALL show stylus name, a bar filled to 75% in `var(--ink-soft)` color, and text "750 h"

#### Scenario: Stylus page bar color changes at threshold
- **WHEN** the stylus has 850 hours (capacity_min 800)
- **THEN** the full bar fill SHALL use `var(--amber-deep)` color

### Requirement: Button styling for touchscreen
Action bar buttons SHALL have no border-radius, no spacing between them, fill their entire grid cell, use DM Mono 14px uppercase with letter-spacing 0.15em, `background: var(--ink)`, `color: var(--paper)`, and `border: 1px solid var(--ink-soft)`.

#### Scenario: Button fills cell with vintage styling
- **WHEN** an action button is rendered
- **THEN** it SHALL fill the full width and height of its grid cell with dark ink background and paper-colored monospace text

### Requirement: Disabled action buttons
The Link button, Re-Link button, and Reset Stylus button SHALL be rendered but have no click handlers attached (future implementation).

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
The UI SHALL establish a WebSocket connection to `/ws` and process incoming events to update the display in real time. WebSocket status events SHALL be ignored when a URL hash is present (dev mode). When no URL hash is present, a `status` event with `{"status": "play", "time": "MM:SS"}` SHALL transition the UI to Play mode and update the playback time shown in the top bar. A `status` event with `{"status": "stop"}` SHALL return the UI to Standby mode and remove the Play-only playback time display.

#### Scenario: Receive stylus_hours event
- **WHEN** the WebSocket sends `{"event": "stylus_hours", "data": {"hours": 89.6, "stylus_id": "1"}}`
- **THEN** the UI SHALL update the stylus hours display

#### Scenario: Receive current_record event
- **WHEN** the WebSocket sends `{"event": "current_record", "data": {"record_id": "1"}}`
- **THEN** the UI SHALL update the current record display

#### Scenario: Receive status play event with time
- **WHEN** the WebSocket sends `{"event": "status", "data": {"status": "play", "time": "00:01"}}` and no URL hash is present
- **THEN** the UI SHALL transition to Play mode
- **AND** the top bar SHALL render `PLAY 00:01`

#### Scenario: Receive status stop event
- **WHEN** the WebSocket sends `{"event": "status", "data": {"status": "stop"}}` and no URL hash is present
- **THEN** the UI SHALL transition out of Play mode
- **AND** the top bar SHALL stop rendering a playback time next to the mode label

#### Scenario: Receive status event with hash
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

### Requirement: UI re-fetches data after sync
After sync completes (success or error), the UI SHALL re-fetch records and styli from the API to ensure all views have current data without requiring a page refresh.

#### Scenario: Sync completes successfully
- **WHEN** the sync SSE stream sends "Sync complete"
- **THEN** the UI SHALL call `fetchRecords()` and `fetchStyli()` to refresh state

#### Scenario: Sync fails
- **WHEN** the sync SSE stream sends "Sync error"
- **THEN** the UI SHALL still call `fetchRecords()` and `fetchStyli()` to refresh state

### Requirement: Single-line record metadata display
Artist names, album titles, and the current track name SHALL remain on a single line anywhere the UI renders record metadata in Standby, Play, Link, or Re-Link mode. The metadata lane SHALL stay constrained to the visible info-column width. When a value exceeds that available width, the UI SHALL preserve the single-line layout and use the approved overflow treatment instead of wrapping onto a second line.

#### Scenario: Metadata fits within the available width
- **WHEN** an artist name, album title, or current track name fits within its container
- **THEN** the text SHALL remain on one line and render without overflow animation

#### Scenario: Metadata overflows in a record view
- **WHEN** an artist name, album title, or current track name is longer than the available width in Standby, Play, Link, or Re-Link mode
- **THEN** the text SHALL remain on one line and use the overflow treatment rather than wrapping onto multiple lines

#### Scenario: Overflow state updates with new content
- **WHEN** the displayed record, side, or track changes
- **THEN** the UI SHALL recalculate whether each affected metadata field needs the overflow treatment for the newly rendered text

#### Scenario: Overflow state updates after layout changes
- **WHEN** fonts finish loading or the viewport layout changes in a way that affects the metadata lane width
- **THEN** the UI SHALL recalculate whether each affected metadata field needs the overflow treatment for the current text

### Requirement: Scoped UI updates for unrelated state changes
The frontend SHALL update only the DOM slices affected by a state change instead of rerunning the full visible view render for every event. Updates that only change top-bar or stylus summary data SHALL NOT rewrite record metadata fields when the visible record, side, and track content are unchanged.

#### Scenario: Temperature refresh updates only top-bar data
- **WHEN** periodic temperature polling returns a new reading while the current mode and visible record metadata are unchanged
- **THEN** the UI SHALL update the temperature display without rewriting the active artist, album, or track metadata DOM

#### Scenario: Stylus-hours update leaves record metadata untouched
- **WHEN** a stylus-hours event is received while a record view is visible and the visible record, side, and track content are unchanged
- **THEN** the UI SHALL update only the stylus-related display elements and SHALL preserve the existing record metadata DOM

### Requirement: Marquee continuity across non-content refreshes
The frontend SHALL preserve active marquee animation state for artist, album, and track fields across updates that do not change the field text or visible lane width. Overflow measurement SHALL rerun when metadata text changes or when a layout-affecting event requires remeasurement.

#### Scenario: Unchanged marquee survives periodic refresh
- **WHEN** a long artist, album, or track field is already animating and an unrelated refresh occurs
- **THEN** the marquee SHALL continue without restarting because the field text was not rewritten

#### Scenario: Metadata change recomputes marquee state
- **WHEN** the visible record, side, or track changes
- **THEN** the affected metadata field SHALL update its text and SHALL recompute whether marquee overflow is required

#### Scenario: Layout change remeasures overflow
- **WHEN** fonts finish loading or the window is resized
- **THEN** the visible marquee fields SHALL remeasure overflow against the current lane width and SHALL keep or clear animation according to the new fit

### Requirement: Play mode — record-not-found fallback
When Play mode is active and no valid current record can be resolved, the UI SHALL render the same gray cover placeholder and "Record Not Found" text used by the standby not-found state. The play view SHALL leave artist, album, and track metadata empty, and the action bar SHALL show no buttons at all.

#### Scenario: Play after record-not-found scan
- **WHEN** the latest scan set the standby state to record-not-found and a `status: "play"` event switches the mode to Play
- **THEN** the play view SHALL show the "Record Not Found" placeholder
- **AND** the play view SHALL NOT show cover art, artist, album title, or track text
- **AND** no action buttons SHALL be visible in the action bar

#### Scenario: Play mode regains a valid record
- **WHEN** play mode is active and a valid current record later becomes available
- **THEN** the play view SHALL switch back to the normal now-playing layout
- **AND** the play action buttons SHALL become visible again


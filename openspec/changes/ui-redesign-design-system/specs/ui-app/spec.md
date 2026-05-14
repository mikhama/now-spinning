## MODIFIED Requirements

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

### Requirement: Persistent top bar
The UI SHALL display a persistent top bar across all modes with `background: var(--paper)`, `border-bottom: 2px solid var(--ink)`, showing the current mode label in DM Mono 11px uppercase on the left and stylus hours in DM Mono 11px `color: var(--ink-mute)` on the right.

#### Scenario: Top bar displays mode label
- **WHEN** the current mode is "Standby"
- **THEN** the top bar SHALL show "STANDBY" in DM Mono uppercase on the left side with ink-colored text

#### Scenario: Top bar displays stylus hours
- **WHEN** a stylus is loaded with 89.6 hours
- **THEN** the top bar SHALL show "89.6 h" in DM Mono on the right in ink-mute color

### Requirement: Button styling for touchscreen
Action bar buttons SHALL have no border-radius, no spacing between them, fill their entire grid cell, use DM Mono 14px uppercase with letter-spacing 0.15em, `background: var(--ink)`, `color: var(--paper)`, and `border: 1px solid var(--ink-soft)`.

#### Scenario: Button fills cell with vintage styling
- **WHEN** an action button is rendered
- **THEN** it SHALL fill the full width and height of its grid cell with dark ink background and paper-colored monospace text

### Requirement: Cover placeholder
Error states that would normally show a cover image SHALL instead display a placeholder box (280×280px) with `background: var(--paper-dark)`, `border: 1px solid var(--ink-soft)`, and descriptive text in DM Mono uppercase `color: var(--ink-mute)` centered inside.

#### Scenario: Cover placeholder renders
- **WHEN** an error state requires a cover placeholder
- **THEN** the placeholder SHALL be a paper-dark box with centered DM Mono uppercase text in ink-mute color

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

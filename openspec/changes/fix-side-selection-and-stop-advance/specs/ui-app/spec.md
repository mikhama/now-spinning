## MODIFIED Requirements

### Requirement: Bottom action bar
The UI SHALL display a bottom action bar with mode-specific buttons in a 4-column grid. Unused slots SHALL be invisible placeholders. Empty Link, Re-Link, and Stylus states SHALL display only the Mode button; they SHALL NOT display a Side button.

#### Scenario: Standby mode actions
- **WHEN** the mode is Standby
- **THEN** the bottom bar SHALL show: [placeholder], Mode, Side, [placeholder]

#### Scenario: Play mode actions
- **WHEN** the mode is Play
- **THEN** the bottom bar SHALL show: <Prev, [placeholder], Side, Next>

#### Scenario: Link mode actions
- **WHEN** the mode is Link and an unlinked record is available
- **THEN** the bottom bar SHALL show: <Prev, Mode, Link, Next>

#### Scenario: Re-Link mode actions
- **WHEN** the mode is Re-Link and a linked record is available
- **THEN** the bottom bar SHALL show: <Prev, Mode, Re-Link, Next>

#### Scenario: Stylus mode actions
- **WHEN** the mode is Stylus and a stylus is available
- **THEN** the bottom bar SHALL show: <Prev, Mode, Reset, Next>

#### Scenario: Link mode with no unlinked records
- **WHEN** the Link screen shows "No unlinked records"
- **THEN** the bottom bar SHALL show only the Mode button
- **AND** no Side button SHALL be visible or actionable

#### Scenario: Other empty browsing modes
- **WHEN** Re-Link has no linked records or Stylus has no styli
- **THEN** the bottom bar SHALL show only the Mode button

## MODIFIED Requirements

### Requirement: Boardless playback correction state
During boardless Play mode, the UI mode state SHALL maintain enough timing state to combine server elapsed time with user side and song corrections. The effective playback position SHALL be recalculated whenever a boardless play status event, Side button click, Prev song click, or Next song click changes playback selection. Prev and Next song clicks SHALL keep the selected side unchanged and wrap the song selection within that side.

#### Scenario: Manual side correction stores offset
- **WHEN** the user manually changes from side "A" to side "B" while the latest server elapsed time is `01:00`
- **THEN** the selected side SHALL become side "B"
- **AND** the manual playback correction offset SHALL be set so the effective playback position is at side "B" for subsequent elapsed-time updates

#### Scenario: Manual song correction stores offset
- **WHEN** the user manually changes from the first song to the second song while the latest server elapsed time is `01:00`
- **THEN** the selected song SHALL become the second song
- **AND** the manual playback correction offset SHALL be set so the effective playback position is at the selected song for subsequent elapsed-time updates

#### Scenario: Manual song wrap corrects playback position on the same side
- **WHEN** the user clicks Next on the final song or Prev on the first song of the selected side during Play
- **THEN** the selected song SHALL wrap to the opposite end of the same side
- **AND** the selected side SHALL remain unchanged
- **AND** the manual playback correction offset SHALL point to the newly selected song's start for subsequent elapsed-time updates

#### Scenario: Stopped playback clears manual song correction
- **WHEN** the user manually selected the second song during Play mode
- **AND** a `status` event with `{"status": "stop"}` is received
- **THEN** the selected song SHALL reset to the first song on the selected side
- **AND** a later `status: "play"` for the same record SHALL start from the selected side's first song

#### Scenario: New scan resets playback correction state
- **WHEN** a valid scan event loads a new current record
- **THEN** the selected side SHALL reset to the first side
- **AND** the selected track SHALL reset to the first track
- **AND** boardless elapsed playback time and manual playback correction offset SHALL be cleared

#### Scenario: Same-record play preserves manually selected side
- **WHEN** the user manually selects side "B" for the current record before a `status: "play"` event arrives
- **THEN** the selected side SHALL remain side "B" after Play mode starts
- **AND** the manual playback correction offset SHALL be set from side "B"
- **AND** the selected song SHALL be the first song unless a song was manually selected before Play mode starts

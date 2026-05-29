## MODIFIED Requirements

### Requirement: Play mode — now playing display
In Play mode, the UI SHALL display the current record's cover image, catalogue number, artist, title, currently playing track name (blue accent), current side label, and prev/next song navigation only when a valid current record with playable side data is loaded.

#### Scenario: Track is playing
- **WHEN** the mode is Play and a record with tracks is loaded
- **THEN** the UI SHALL show the cover image, `#<id>`, artist, title, track name, side label, and `<Prev` / `Next>` buttons

#### Scenario: Side switching in Play
- **WHEN** the user clicks the Side button in Play mode while a valid record is loaded
- **THEN** the UI SHALL cycle to the next side and reset the track index to `0`

## ADDED Requirements

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
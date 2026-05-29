## MODIFIED Requirements

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
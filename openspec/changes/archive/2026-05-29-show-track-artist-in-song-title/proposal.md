## Why

Some records in the synced collection include a per-track artist that differs from the album artist, but Play mode currently renders only the track title. That drops important context for compilations, soundtrack sides, and featured tracks, making the now-playing line less accurate exactly where users rely on it most.

## What Changes

- Update Play mode's now-playing text contract so a track with its own artist is rendered as `{song_title} ({artist})`.
- Keep the current title-only rendering for tracks that do not provide a separate artist.
- Limit the change to playback metadata formatting; record, API, and sync data structures remain unchanged.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `ui-app`: Play mode track text must append the track-level artist in parentheses when the current track supplies a separate artist from the album-level record artist.

## Impact

- Affected frontend rendering in `ui/app.js` and the Play mode metadata lane in `ui/index.html` / `ui/style.css`.
- Affected OpenSpec contract in `ui-app`.
- No API, database, or sync-pipeline schema changes are expected because track `artist` already exists in the data model.
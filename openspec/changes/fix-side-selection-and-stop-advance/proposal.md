## Why

After a side has been selected or advanced, an NFC read error followed by another scan of the same record resets the display to side A. The current stop rule also misses ordinary early stops, manual side changes in Play mode need to remain effective, and the empty Link screen exposes a Side button from the Standby action bar.

## What Changes

- Preserve the selected side when an NFC read error is followed by a successful scan of the same linked record. A different or newly selected record still starts on its first side.
- Advance to the next side on stop when playback has lasted at least 60 seconds, as well as when it stops within the final 20 seconds of the estimated side duration or later.
- Make Play-mode Side clicks update the selected side and playback correction reliably, including after a side-duration overrun.
- Show a Mode-only action bar when Link mode has no unlinked records; use that fallback for other empty browsing modes too.
- Add regression coverage for these state transitions and action-bar visibility.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `mode-state-machine`: Keep record identity and side selection through a transient NFC read error and same-record scan; broaden stopped-playback side advancement to include one minute of elapsed playback.
- `ui-app`: Specify the Mode-only action bar for empty browsing screens; the existing Play-mode manual side correction requirement is exercised by this fix.

## Impact

- Frontend state transitions, playback offset handling, and action-bar selection in `ui/app.js` and `ui/index.html`.
- Frontend behavioral tests. No API, database, dependency, or hardware integration changes.

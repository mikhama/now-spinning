## Why

The Play screen currently moves to another record side when Next is pressed on the last song or Prev is pressed on the first song. Song navigation should cycle through the songs on the selected side; these buttons should never change the selected side.

## What Changes

- Make Next and Prev wrap between the first and last songs of the currently selected side.
- Preserve the selected side and its label during song navigation, including after later elapsed-time updates.
- Keep manual playback position correction aligned with the song selected after wrapping.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui-app`: Define Play song navigation as cycling within the selected side.
- `mode-state-machine`: Require manual song selection to keep the current side while correcting playback position.

## Impact

The change affects Play navigation in `ui/app.js` and its browser-side behavior checks. It does not change the API, record data, side button, or automatic side advancement on stop.

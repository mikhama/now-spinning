## 1. Record identity and playback

- [x] 1.1 Preserve the selected side across an NFC read error and a repeat scan of the same linked record; reset selection for a different or invalid record.
- [x] 1.2 Advance once on stop after at least 60 seconds of raw playback or within the final 20 seconds of a side with a known positive duration; keep the side for brief earlier stops.
- [x] 1.3 Rebase manual side changes during Play mode so the selected side, track, and label stay aligned through later elapsed-time updates, including overrun and wraparound.

## 2. Empty-state action bar

- [x] 2.1 Add a Mode-only action group for empty Link, Re-Link, and Stylus states, with the Mode button wired to the existing cycle action.

## 3. Verification

- [x] 3.1 Add behavioral regression tests for the scan/error/recovery sequence, new-record reset, stop thresholds, manual Play-mode side changes, and empty-state action visibility.
- [x] 3.2 Run targeted and existing tests, inspect the rendered action bar, and validate the OpenSpec change.

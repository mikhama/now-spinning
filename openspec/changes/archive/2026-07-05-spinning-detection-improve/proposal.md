## Why

The runtime playback detector still uses a single high RPM threshold while the calibration tool now uses trend-based start and stop detection. Bringing production detection in line with the validated calibration behavior should reduce noisy play/stop transitions and apply the newly measured tonearm delay.

## What Changes

- Update runtime playback start detection to use the same RPM trend rules as the calibration script: RPM above `1000` plus either a greater-than-`500` RPM increase over a `3` second observation window, or an already-spinning steady window that stays within `500` RPM increase/decrease and is not strictly decreasing.
- Update runtime stopped detection to use the same calibration stop rules: RPM below `1000`, or at least `4` consecutive strictly decreasing readings with a total drop of at least `1000` RPM.
- Change the runtime automatic tonearm delay constant to `TONEARM_DELAY_AUTO = 12065`.
- Preserve existing playback status event behavior: emit play only after spinning detection plus tonearm delay, emit elapsed play updates while playing, and emit a single stop event when stopped.

## Capabilities

### New Capabilities

### Modified Capabilities
- `playback-status-detection`: Change backend runtime playback start and stop requirements from single-threshold checks to the validated calibration trend rules, and update the automatic tonearm delay constant.

## Impact

- Affects backend playback status detection logic in `api/playback_status.py`.
- Affects playback status tests under `tests/`.
- Aligns runtime behavior with the archived `calibration-improvement` change and current `spinning-detection-calibration` requirements.
- Does not change APIs, WebSocket payload shape, database schema, UI behavior, or the calibration script requirements.

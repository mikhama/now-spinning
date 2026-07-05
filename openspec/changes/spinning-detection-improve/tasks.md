## 1. Tests

- [x] 1.1 Update playback status tests to assert `TONEARM_DELAY_AUTO = 12065`.
- [x] 1.2 Add detector coverage for RPM below or equal to `1000` producing no play event.
- [x] 1.3 Add detector coverage for insufficient spin-up increase over the `3` second observation window.
- [x] 1.4 Add detector coverage for valid spin-up increase starting the tonearm delay and emitting play only after `12065` milliseconds.
- [x] 1.5 Add detector coverage for already-spinning steady RPM starting the tonearm delay.
- [x] 1.6 Add detector coverage for strictly decreasing steady-range RPM not starting the tonearm delay.
- [x] 1.7 Add detector coverage for stopped detection before tonearm delay completion resetting pending playback without emitting play or stop.
- [x] 1.8 Add detector coverage for stopped detection during playback from RPM below `1000`.
- [x] 1.9 Add detector coverage for stopped detection during playback from at least `4` strictly decreasing samples with at least `1000` RPM total drop.
- [x] 1.10 Update publisher logging tests so the logged `spinning` value reflects runtime spin-up classification rather than a single RPM threshold comparison.

## 2. Runtime Detection

- [x] 2.1 Update playback detection constants in `api/playback_status.py`, including `TONEARM_DELAY_AUTO = 12065` and calibration-equivalent trend constants.
- [x] 2.2 Add a runtime RPM sample representation and spin-up classifier matching the calibration script logic.
- [x] 2.3 Add a runtime stopped classifier matching the calibration script logic.
- [x] 2.4 Add sample pruning that preserves enough history for both the `3` second spin-up observation window and gradual stopped detection.
- [x] 2.5 Update `PlaybackStatusDetector.sample()` so the stopped state starts tonearm delay only after spin-up classification succeeds.
- [x] 2.6 Update pending-delay behavior so stopped classification resets pending playback without emitting events.
- [x] 2.7 Update playing behavior so stopped classification emits exactly one stop event, otherwise elapsed play updates continue as before.
- [x] 2.8 Update `publish_playback_status_once()` logging to use the detector's runtime spinning classification.

## 3. Verification

- [x] 3.1 Run the playback status tests and fix failures caused by the new detection behavior.
- [x] 3.2 Run the full Python test suite.
- [x] 3.3 Run `openspec validate spinning-detection-improve --strict`.

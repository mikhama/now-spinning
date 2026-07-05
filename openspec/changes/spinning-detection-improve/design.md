## Context

Runtime playback status detection lives in `api/playback_status.py`. Before this change, it modeled playback with a simple state machine that started the tonearm delay after a single high-RPM sample, then stopped playback as soon as a later sample fell below that same cutoff.

The archived `calibration-improvement` change updated `exp/spinning_detection_calibration.py` to use trend-based helpers for spin-up and stop detection. Those helpers now represent the validated hardware behavior: spinning starts from either an active RPM increase or an already-steady spinning window above `1000` RPM, and stopped detection can trigger before RPM fully drops below threshold when the latest readings are strictly decreasing enough. This change promotes those same rules into runtime detection and updates the measured automatic tonearm delay to `12065` milliseconds.

## Goals / Non-Goals

**Goals:**

- Align runtime start detection with calibration spin-up rules.
- Align runtime stop detection with calibration stopped rules.
- Update `TONEARM_DELAY_AUTO` to `12065`.
- Preserve the existing backend status event shape: `status: "play"` with `time` and `status: "stop"` without adding new payload fields.
- Keep the playback detector unit-testable without GPIO hardware.

**Non-Goals:**

- Change WebSocket/API payload shape, frontend behavior, or database schema.
- Change the calibration script requirements or manual calibration workflow.
- Add persistence or UI controls for tuning detection constants.
- Rework GPIO pulse counting or the one-second runtime polling cadence.

## Decisions

### Share the calibration detection model in runtime code

Add runtime equivalents of the calibration sample-history rules in `api/playback_status.py`: an RPM sample value with timestamp, a spin-up classifier, a stopped classifier, and pruning helpers for bounded sample history. The constants should match calibration behavior: `MIN_SPINNING_RPM = 1000`, `SPIN_UP_OBSERVATION_WINDOW_SECONDS = 3`, `SPIN_UP_RPM_INCREASE = 500`, `STOPPED_RPM_THRESHOLD = 1000`, `STOPPED_SAMPLE_COUNT = 4`, and `STOPPED_TOTAL_RPM_DROP = 1000`.

Alternative considered: keep the `4500` threshold and only update the tonearm delay. That would apply the new measured delay but leave the runtime detector using behavior that calibration deliberately replaced as too noisy.

### Preserve the detector state machine, but change its transition predicates

Keep the state machine, but rename the pending state to match the new behavior: `stopped`, `tonearm_delay_pending`, and `playing`. The runtime no longer has a single threshold-crossing state because playback starts from the spin-up classifier.

In `stopped`, append each sample to history and move to the pending-delay state only when the spin-up classifier returns true. At that point, set `tonearm_delay_started_at` from the current sample time and continue waiting for `TONEARM_DELAY_AUTO`.

In `tonearm_delay_pending`, evaluate stopped detection before delay completion. If stopped is detected before the delay elapses, reset to `stopped` without emitting a stop event. If the delay elapses while stopped detection has not triggered, enter `playing` and emit `play` with `time: "00:00"`.

In `playing`, evaluate stopped detection on each sample. When stopped is detected, reset playback timing state and emit exactly one `stop` event. Otherwise, keep emitting elapsed `play` updates only when the elapsed playback second advances.

Alternative considered: replace the state machine with direct helper outputs. The delay window and elapsed-time event deduplication still require state, so retaining the current structure keeps the behavioral surface smaller.

### Use one runtime sample history for both start and stop checks

Store recent samples on the detector instance and update the history inside `sample(rpm, now=None)`. Spin-up pruning can keep enough data for the `3` second observation window and at least `4` stop samples. Stop pruning should preserve the latest strictly decreasing run so gradual spin-down over more than `3` seconds can still trigger stopped detection, matching the calibration helper tests.

Alternative considered: maintain separate start and stop histories. That would make helper code easier to reason about in isolation, but it creates more state to reset and raises the risk that runtime behavior drifts from the calibration script.

### Remove obsolete threshold-era runtime API

Remove the obsolete `SPINNING_RPM_THRESHOLD` constant and `rpm_threshold` constructor argument from runtime playback detection. The runtime implementation should expose the named trend constants that now define behavior. Logging in `publish_playback_status_once` should report the classification result rather than a single threshold comparison; callers should still see one sensor log per sample and event logs when start/stop events are broadcast.

Alternative considered: keep `SPINNING_RPM_THRESHOLD` and `rpm_threshold` as compatibility aliases. That would avoid API churn for any unknown callers, but repo search shows no remaining use and the names now misrepresent runtime behavior.

## Risks / Trade-offs

- [Risk] Duplicating calibration helper logic in runtime code can drift later. -> Mitigation: add parallel unit tests in `tests/test_playback_status.py` for the same representative start/stop scenarios covered by calibration tests.
- [Risk] The steady-spinning branch can classify playback as pending when the app starts after the platter is already moving. -> Mitigation: this is intentional and matches calibration; the tonearm delay still prevents immediate play emission.
- [Risk] A strictly decreasing run can emit stop before RPM falls below `1000`. -> Mitigation: require at least `4` consecutive decreasing readings and at least `1000` RPM total drop, matching the validated calibration rule.
- [Risk] Existing tests that assert `4500` threshold behavior will become invalid. -> Mitigation: update tests to assert trend-based behavior and the new `12065` delay constant.

## Migration Plan

1. Add or update playback detector tests for trend-based spin-up, already-spinning steady detection, strict-decrease rejection during startup, trend-based stop, pending-delay reset on stop, event deduplication, and `TONEARM_DELAY_AUTO = 12065`.
2. Update `api/playback_status.py` constants and detector internals to use sample history and the calibration-equivalent classifiers.
3. Update publisher logging expectations so the logged `spinning` value reflects runtime classification instead of a single RPM threshold comparison.
4. Run the Python test suite and OpenSpec validation for `spinning-detection-improve`.

Rollback is limited to reverting `api/playback_status.py` and related tests; no schema, API, or UI migration is required.

## Open Questions

- None currently. The requested calibration behavior and tonearm delay value are specified.

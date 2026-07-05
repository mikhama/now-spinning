## Context

The experimental calibration flow currently lives in `exp/spinning_detection_calibration.py`. It samples GPIO pulses once per second, converts the pulse count to RPM, and starts the tonearm delay timer as soon as a single sample reaches `SPINNING_RPM_THRESHOLD`.

This change keeps calibration separate from runtime playback detection. The production app logic in `api/playback_status.py` continues to use its existing threshold/delay behavior until a later change deliberately updates it.

## Goals / Non-Goals

**Goals:**
- Make calibration spin-up detection depend on a short RPM trend instead of a single sample.
- Keep the operator confirmation step for needle-on-platter timing.
- Add stopped detection to the calibration tool so operators can observe whether the same sampling data identifies spin-down reliably.
- Keep thresholds and timing values visible as top-level calibration constants.

**Non-Goals:**
- Do not change backend runtime playback detection behavior.
- Do not change frontend status handling, event payloads, or persisted data.
- Do not introduce new hardware dependencies beyond the existing GPIO pulse counter.

## Decisions

### Use a rolling RPM sample history inside the calibration script

The calibration script should keep recent `(timestamp, rpm)` samples while it polls the sensor. Spinning detection can then compare the current sample with an older sample at least 3 seconds back and require:

- current RPM is above `1000`
- current RPM either increased by more than `500` RPM over that 3 second window, or both the current and comparison RPM are above `1000`, stayed within `500` RPM increase/decrease over that window, and the window is not strictly decreasing

This covers both cases operators need during calibration: catching active spin-up, and recognizing a platter that was already spinning steadily when the script started. A platter that is continuously slowing down is not considered steady even if the net RPM drop is still within 500 RPM.

Alternative considered: continue using one threshold crossing. That is simpler but preserves the noisy behavior this change is meant to remove.

### Add explicit helper functions for spin-up and stop classification

Implement small helpers such as `is_spinning(samples)` and `is_stopped(samples)` so the conditions are testable without GPIO hardware. The calibration loop should print measured RPM and classification state, while these helpers own the trend rules.

Alternative considered: inline the checks inside the polling loop. That would be shorter, but harder to test and easier to misread because the two rules use different windows.

### Treat stopped as either below-threshold or sustained decreasing trend

Stopped detection should return true when the latest RPM is below `1000`, or when 4 consecutive readings are strictly decreasing and the total drop from the first to the fourth reading is at least `1000` RPM.

The decreasing rule should operate on the latest 4 samples. The below-threshold rule should be immediate so a clearly stopped platter does not need to wait for 4 more samples.

Alternative considered: require a per-step minimum drop. The clarified requirement uses a total drop across 4 decreasing readings, which avoids rejecting real spin-down sequences where one interval is smaller but the overall direction is clear.

### Preserve manual delay measurement once spinning is detected

When the spin-up helper classifies the platter as spinning, the script starts the delay timer and prompts the operator to press Enter when the needle reaches the platter. The elapsed milliseconds output remains the calibration result.

Alternative considered: stop the timer automatically from RPM behavior. That would measure platter state, not needle-on-platter timing, and would remove the manual observation this calibration is intended to capture.

## Risks / Trade-offs

- [Risk] One-second sampling may make the 3 second spin-up window approximate rather than exact. -> Mitigation: compare against the oldest retained sample at or before the 3 second lookback when available, and keep console output clear about sample values.
- [Risk] Starting the script after the platter is already spinning can produce no large positive RPM change. -> Mitigation: treat above-threshold stable RPM within the spin-up delta as spinning too.
- [Risk] A continuously slowing platter can have a small enough net drop to look stable. -> Mitigation: reject strictly decreasing observation windows from the already-spinning steady rule.
- [Risk] Sensor noise could make a real spin-down sequence fail the strictly-decreasing rule. -> Mitigation: keep the below-1000 RPM stopped threshold as an immediate fallback and make the trend constants easy to adjust.
- [Risk] Calibration behavior could drift from runtime playback detection. -> Mitigation: document and keep the scope explicitly limited to `exp/spinning_detection_calibration.py`; runtime changes require a separate proposal.

## Why

The current calibration script starts timing from a single threshold crossing, which can be too noisy for reliable turntable calibration. The calibration flow needs explicit checks for sustained spin-up and sustained spin-down so the measured delay is based on the platter's actual motion pattern without changing the app's runtime detection logic yet.

## What Changes

- Update the experimental calibration script to classify the platter as spinning only when RPM is above 1000 and has increased by more than 500 RPM over a 3 second window.
- Keep the manual needle-on-platter confirmation flow: once spinning is detected, the script waits for the operator to press the button/Enter when the needle reaches the platter, then reports the measured delay.
- Add stopped detection to the calibration tool: classify the platter as stopped when RPM drops below 1000, or when 4 consecutive readings are strictly decreasing and the total drop from the first to the fourth reading is at least 1000 RPM.
- Scope the change to the calibration tool only; the current app spinning detection logic is not changed by this proposal.

## Capabilities

### New Capabilities

### Modified Capabilities
- `spinning-detection-calibration`: Change calibration requirements from a single threshold crossing to trend-based spinning and stopped detection checks in the experimental calibration script.

## Impact

- Affects the experimental calibration script under `exp/`.
- May affect console prompts and calibration output messages used during manual calibration.
- Does not change app runtime spinning detection, APIs, database schema, or production UI behavior.

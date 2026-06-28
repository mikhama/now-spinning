## Why

Spinning detection depends on hardware-specific sensor readings and tonearm timing, so fixed constants are hard to choose reliably without a repeatable calibration aid. A small experimental helper should make it easier to find the threshold that means "spinning" and measure how long after that threshold the stylus reaches the platter.

## What Changes

- Add a helper script under `exp/` for calibrating spinning detection constants during manual hardware testing.
- Let the operator set the spinning threshold constant manually in the script.
- Provide a console calibration flow for the timing constant: when the threshold is reached, the script announces that timing has started, waits for the operator to press Enter when the needle reaches the platter, and reports the elapsed milliseconds.
- Keep the helper scoped to experimentation and calibration; no production behavior changes are introduced by this change.

## Capabilities

### New Capabilities
- `spinning-detection-calibration`: Defines an experimental console workflow for deriving spinning detection constants from real turntable behavior.

### Modified Capabilities

None.

## Impact

- Adds or updates files under `exp/`, likely near the existing platter spinning experiment code.
- May reuse existing sensor-reading helpers or GPIO access used by current platter spinning detection experiments.
- No API, database, or UI changes are expected.

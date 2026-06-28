## Context

The repository already has `exp/platter_spinning.py`, which reads a GPIO digital input, counts activations, and prints an estimated RPM every five seconds. The new helper is an experimental calibration tool for the same hardware context, not production detection logic. It should support hands-on testing where an operator watches the tonearm and provides the moment when the needle reaches the platter.

The calibration has two constants:

- A manually configured spinning threshold that decides when the platter should be considered spinning.
- A measured delay, in milliseconds, from the moment that threshold is reached until the needle reaches the platter.

## Goals / Non-Goals

**Goals:**

- Provide a console script under `exp/` that can be run on the Raspberry Pi with the same GPIO sensor setup used by the current platter spinning experiment.
- Let the operator edit the threshold constant directly in the script before running it.
- Continuously sample pulse-derived RPM or rate values until the configured threshold is reached.
- Clearly tell the operator when threshold detection has happened and timing has started.
- Wait for the operator to press Enter when they see the needle reach the platter, then print the elapsed time in milliseconds.

**Non-Goals:**

- Do not change production application behavior.
- Do not persist calibration results automatically.
- Do not add a UI, API, or database model for calibration.
- Do not try to detect tonearm position automatically; the operator supplies that event manually.

## Decisions

- Create a separate experimental script instead of expanding production code.
  - Rationale: calibration requires human observation and hardware-specific iteration, so keeping it under `exp/` avoids coupling this workflow to runtime behavior.
  - Alternative considered: expose calibration through the app UI. That would add unnecessary surface area before the correct constants are known.

- Reuse the existing GPIO pulse-counting approach from `exp/platter_spinning.py`.
  - Rationale: the current experiment already proves the basic sensor path: `gpiozero.DigitalInputDevice`, activation callbacks, pulse counting, elapsed time, and RPM estimation.
  - Alternative considered: introduce a new sensor abstraction. That would be premature for an experimental script.

- Make the spinning threshold a top-level constant in the script.
  - Rationale: the user wants to choose this value manually, and a visible constant is simple to adjust during repeated runs.
  - Alternative considered: accept the threshold as a CLI flag. That is more flexible, but less direct than editing the value in one obvious place for early calibration.

- Start tonearm delay timing only after a sampled value reaches the threshold.
  - Rationale: the timing constant must measure the delay after the system has decided the platter is spinning, not from script start.
  - Alternative considered: ask the operator to press Enter twice, once when spinning starts and once when the needle reaches the platter. That would calibrate a different event and introduce more human timing error.

- Use blocking console input for the needle-on-platter event.
  - Rationale: the calibration event is visual and manual, so `input()` gives a clear operator-controlled stop point while keeping implementation simple.
  - Alternative considered: use keypress detection without Enter. That would need more terminal handling and is not necessary for a helper script.

## Risks / Trade-offs

- Human reaction time affects the measured delay -> Run the calibration multiple times and choose a representative or conservative value.
- RPM estimates can be noisy if the sample window is too short -> Keep a configurable sample interval and default to a stable value similar to the existing five-second experiment.
- GPIO access requires running on the target hardware -> Keep the script isolated under `exp/` and document expected hardware assumptions in the script output.
- The correct threshold unit may depend on the existing sensor behavior -> Name the constant and output in terms of the measured value, and keep the calculation close to the current experiment's RPM-style estimate.

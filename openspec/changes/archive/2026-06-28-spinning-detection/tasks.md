## 1. Existing Experiment Review

- [x] 1.1 Review `exp/platter_spinning.py` to confirm the GPIO pin, pull-up setting, pulse callback, and RPM calculation currently used for platter sensing.
- [x] 1.2 Choose the new calibration script filename under `exp/` and keep it separate from existing experiments.

## 2. Calibration Script

- [x] 2.1 Create the experimental console calibration script under `exp/`.
- [x] 2.2 Add top-level constants for the GPIO pin, sample interval, and manually editable spinning threshold.
- [x] 2.3 Implement pulse counting with `gpiozero.DigitalInputDevice` using the existing platter sensing pattern.
- [x] 2.4 Implement repeated sampling that prints the measured spinning value while it remains below the threshold.
- [x] 2.5 Start the tonearm delay timer only after the measured value reaches or exceeds the configured threshold.
- [x] 2.6 Print a clear console message when threshold detection happens and timing starts.
- [x] 2.7 Wait for the operator to press Enter when the needle reaches the platter.
- [x] 2.8 Print the elapsed tonearm delay in milliseconds after Enter is pressed.
- [x] 2.9 Add concise run instructions to `README.md`, including the command to run the calibration tool, the need to edit the threshold constant before running, and the requirement to run on the Raspberry Pi hardware with the platter sensor connected.

## 3. Verification

- [x] 3.1 Run a syntax check for the new script.
- [x] 3.2 Confirm the script can be inspected without side effects when imported or syntax-checked.
- [x] 3.3 Verify the `README.md` run instructions mention that live GPIO behavior requires running the script on the Raspberry Pi hardware.

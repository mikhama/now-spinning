## 1. Calibration Constants and Helpers

- [x] 1.1 Add top-level constants for minimum spinning RPM, spin-up observation window, spin-up RPM increase, stopped RPM threshold, stopped sample count, and stopped total RPM drop in `exp/spinning_detection_calibration.py`.
- [x] 1.2 Add a rolling RPM sample representation that records sample time and measured RPM without changing GPIO pulse counting.
- [x] 1.3 Implement a testable spinning classification helper that returns true only when RPM is above `1000` and has increased by more than `500` RPM across a `3` second window.
- [x] 1.4 Implement a testable stopped classification helper that returns true when RPM is below `1000` or when the latest `4` readings are strictly decreasing with at least `1000` RPM total drop.

## 2. Calibration Flow

- [x] 2.1 Update the polling loop to maintain recent RPM samples and use the spinning helper before starting the tonearm delay timer.
- [x] 2.2 Preserve the manual operator prompt and elapsed millisecond output after spinning is detected.
- [x] 2.3 Add stopped-state console reporting to the calibration tool without changing production playback detection logic.
- [x] 2.4 Keep the implementation scoped to `exp/spinning_detection_calibration.py` and avoid modifying `api/playback_status.py`.

## 3. Verification

- [x] 3.1 Add unit coverage for spin-up detection below or equal to `1000` RPM, insufficient increase, and valid increase over the observation window.
- [x] 3.2 Add unit coverage for stopped detection below `1000` RPM, valid strictly decreasing readings with sufficient total drop, non-decreasing readings, and insufficient total drop.
- [x] 3.3 Run the relevant Python test suite and fix any failures caused by the calibration changes.

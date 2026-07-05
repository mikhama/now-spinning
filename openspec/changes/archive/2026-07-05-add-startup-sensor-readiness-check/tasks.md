## 1. Sensor Readiness Helpers

- [x] 1.1 Add an RPM sensor readiness probe in `api/playback_status.py` that creates the hardware reader, reads one sample, closes the reader, and raises on setup or sampling failure.
- [x] 1.2 Add an NFC sensor readiness path that forces the hardware backend to initialize without waiting for an NFC card.
- [x] 1.3 Wrap readiness failures in clear startup errors that identify which sensor failed.

## 2. Startup Orchestration

- [x] 2.1 Add a testable API startup function in `api/main.py` that runs readiness checks before starting publishers, coordinators, or Flask.
- [x] 2.2 Skip physical sensor readiness checks when `BOARDLESS_MODE=true`.
- [x] 2.3 Update the `python -m api.main` entry point to use the new startup function and allow readiness exceptions to exit the script.

## 3. Tests

- [x] 3.1 Add playback status tests for successful RPM readiness, reader initialization failure, sample failure, and reader cleanup.
- [x] 3.2 Add API startup tests proving hardware-mode NFC readiness failure prevents worker/server startup.
- [x] 3.3 Add API startup tests proving hardware-mode RPM readiness failure prevents worker/server startup.
- [x] 3.4 Add API startup tests proving boardless mode skips physical sensor readiness and can start.
- [x] 3.5 Update any existing tests that expected missing RPM hardware to be tolerated in hardware mode.

## 4. Verification

- [x] 4.1 Run the focused unit tests for playback status, NFC/startup behavior, and API startup.
- [x] 4.2 Run the full test suite.
- [x] 4.3 Run `openspec status --change "add-startup-sensor-readiness-check"` and confirm the change is apply-ready.

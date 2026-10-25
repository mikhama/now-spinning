## 1. Reader cleanup

- [x] 1.1 Add safe backend close without reader initialization. Use driver close and provide boardless cleanup.
- [x] 1.2 Test repeated close, RF-off failure, transport close, and cleanup without a backend.

## 2. NFC worker

- [x] 2.1 Stop new work, discard queued work, interrupt the polling pause, and close in the worker finally block.
- [x] 2.2 Log mode changes, operation outcomes, and cleanup results with original exception details. Correct the I2C diagnostic.
- [x] 2.3 Test idle, read, and write shutdown. Verify queued work rejection, last-record retention, and confirmed write completion.

## 3. Application exit

- [x] 3.1 Retain the NFC thread and use one cleanup path for signals, server exit, process exit, and startup failure.
- [x] 3.2 Enforce one five-second wait, including reader cleanup. Make repeated calls and signals safe. Return JSON 503 for new NFC mode and write requests during shutdown.
- [x] 3.3 Add a subprocess regression for termination during a Standby read. Test blocked workers, startup failure, boardless mode, and stylus persistence.

## 4. Validation

- [x] 4.1 Run the Python suite, relevant JavaScript tests, strict OpenSpec validation, and git diff --check. Record local results separately.

## Follow-up on the Pi

The user will deploy and check the application. The user declined the ten-run reporting procedure. No deployment or further check of the deployment procedure is required from Codex.

The reported sequences remain useful for the Pi check:

- Scan → play → stop → Standby → Exit → reopen.
- Scan 1 → 43 → 15 → 23 → 1 → Exit → reopen.

Keep this change open. Do not sync specifications or archive it. The hardware fault remains unverified until the user checks it on the Pi.

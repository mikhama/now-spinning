## 1. Driver protocol and RF lifecycle

- [x] 1.1 Implement matching RF controls, finite initialization, RF-off confirmation, and cleanup-before-close for I2C and UART.
- [x] 1.2 Implement monotonic shared deadlines, expected-command/frame validation, delayed UART response handling, and explicit transport/protocol errors.
- [x] 1.3 Implement at-most-200-ms detection probes with RF-off after absence/failure and one-second RF-off pauses during long waits.
- [x] 1.4 Verify both drivers with fake transports and clocks, including RF command bytes, retries, shared budgets, ACK delays, empty responses, stale/malformed frames, and close failures.

## 2. Backend and coordinator

- [x] 2.1 Keep RF active through complete authentication/read/write and add finally cleanup on success, timeout, failure and interruption with explicit chained RF-off errors.
- [x] 2.2 Set the coordinator default detection timeout to 200 ms, retain the one-second post-operation pause, and atomically claim serialized work without hardware calls in mode handlers.
- [x] 2.3 Verify multi-page/block transfers, no-card/long-write RF-off pauses, inactive Play/Sync/Stylus/Link/Re-link/unknown modes, and transitions before and during an attempt.
- [x] 2.4 Retain record replacement, duplicate suppression, last-record preservation, public signatures, boardless behavior, payload and write-serialization regressions.

## 3. Documentation and validation

- [x] 3.1 Keep timing and cleanup details in the change design and remove the added README hardware verification block as requested.
- [x] 3.2 Run focused NFC tests, the complete Python suite, relevant API/UI checks, and strict noninteractive OpenSpec validation; record results separately from hardware status.

Leave this change ready for review and unarchived. Do not change or archive `keep-last-record-on-nfc-read-error`.

After deployment, use the short end-to-end smoke check in `verification.md`.
This manual follow-up does not block implementation and requires no measuring equipment.

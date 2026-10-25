## Context

The NFC worker is a daemon thread. The application does not retain its reference. Exit hooks only save stylus usage. Process termination can therefore skip the backend RF cleanup. Existing drivers already attempt RF-off and close the transport after an error.

## Goals / Non-Goals

**Goals:** Stop new work at shutdown. Complete the active operation and close the reader in the worker. Wait up to five seconds, including reader cleanup. Preserve stylus usage, confirmed write completion, the last record after a read error, and the Exit response. Identify errors before exit and during cleanup.

**Non-Goals:** Change NFC timing, payloads, bus configuration, reset hardware, or add bus recovery. Do not claim that the I2C fault is fixed from local tests.

## Decisions

1. Add `Pn532Backend.close()` and boardless close. `close_backend()` uses only the existing backend. Clear its reference before close so repeated calls do not repeat hardware commands, including after close failure. Use the existing driver close method. Do not add another RF command path.
2. Use a terminal stop event under the coordinator state lock. Reject mode and write requests after stop. Clear queued writes. The active request keeps its completion and persistence behavior. The worker uses an event wait for its polling pause and closes the backend in `finally`. Record the cleanup result. A mode change cannot clear the stop event.
3. Retain the worker thread. One application cleanup function handles signals, normal server return, startup failure, and `atexit`. Stop the worker, then join against one five-second deadline. If the worker never started, start it in the stopped state to close any existing backend in its `finally` block. This also bounds startup-failure cleanup and keeps hardware close in a worker. If the deadline expires, log incomplete cleanup and continue exit without another reader command. Repeated cleanup calls do not start another wait or close. Repeated signals during cleanup do not interrupt the first cleanup.
4. Keep the Exit route persistence check and delayed runner termination. The runner signal invokes the common application cleanup. Reject new NFC requests with JSON 503, including a request that races with stop.
5. Log mode transitions, read/write outcomes, worker exit, reader close, and timeout. Include exception tracebacks so the original exception, errno, and transport stage remain available through exception chains. The I2C diagnostic prints the actual bus error and errno. Keep existing driver deadlines and transport-stage error messages.

## Risks / Trade-offs

- A blocked read, write, or close can exceed five seconds. The process can exit with incomplete cleanup. The log identifies this result. The main thread must not issue a competing hardware command.
- A write can wait for a tag for 30 seconds. Keep this behavior. If it completes within the shutdown budget, persist and broadcast its confirmed result before close.
- Forced termination, such as SIGKILL or power loss, cannot run Python cleanup. Use the normal runner termination path for verification.
- Local tests cannot prove recovery on the Pi. Keep the hardware checks separate and pending until measurements are available.

## Migration Plan

Run local checks. The user will deploy and check the application through their existing Pi workflow. The user declined the ten-run reporting procedure. The two reported sequences and tag-present and tag-absent exits remain useful for that check. Logs distinguish errors before exit from cleanup failures. Revert this change if the shutdown path causes a regression.

## Open Questions

Does the I2C failure begin before exit, during cleanup, or at reopen? Pi logs and repeated sequence checks must answer this question.

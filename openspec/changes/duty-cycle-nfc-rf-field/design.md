## Context

Both drivers leave passive activation retries infinite and never explicitly disable RF. I2C spends the timeout twice (ACK and response); UART can return after ACK alone and neither validates response command/checksums. The single NFC coordinator worker already serializes reads/writes and sleeps one second after each tick. Mode handlers only update state. The existing last-record retention change is already implemented and stays separate.

## Goals / Non-Goals

**Goals:** Confirm RF-off at initialization, between attempts, after all operations, at idle, and before transport close; cap each detection command at 200 ms using monotonic time; preserve complete payload transfers, signatures, payloads, events, and record retention.

**Non-Goals:** Change tag encoding, UI, event schemas, boardless input, or archive either active change. Instrumented RF and temperature/current measurements are not required.

## Decisions

1. Share PN532 frame validation, command constants, card helpers, and RF lifecycle in a small driver base; keep transport operations in I2C/UART subclasses. This avoids divergent lifecycle implementations. Use a shared error module re-exported by `lib.nfc` so driver failures are `NfcError` without circular imports.
2. Configure SAM, `RFConfiguration(0x05, 0xFF, 0x01, 0x00)`, and confirmed RF-off before construction succeeds. Both drivers expose `set_rf_field(enabled: bool) -> bool` using item `0x01` and byte `0x00`/`0x01`. Empty configuration responses are success; missing or unexpected payloads fail. Constructor failures attempt cleanup and always close the transport.
3. Use a single monotonic command deadline through transmission, ACK, and expected response. UART keeps buffering after ACK and across fragmented frames. Validate frame length, checksums, postamble, direction, and response command. Discard valid unrelated responses while waiting; malformed, missing, or transport-failed replies raise `NfcError`. A new command aborts unfinished PN532 work (NXP manual section 6.2.2.2); RF-off cleanup therefore also terminates timed-out detection.
4. `wait_for_card` enables RF per probe, gives detection `min(0.2, remaining)` seconds, disables RF after absence/failure, and pauses RF-off for one second (capped by remaining interactive deadline). A found card transfers RF ownership to the backend until authentication and all pages/blocks finish. Public 30-second interactive waits stay intact; the coordinator supplies 200 ms by default.
5. Backend read/write use `finally` RF-off cleanup, including interruption. Cleanup failures explicitly report RF-off failure; Python exception context retains the original failure. Failed classic authentication or malformed UTF-8/short data must not yield a successful partial record.
6. Mode changes update state under the coordinator lock and never send hardware commands. The worker checks eligibility atomically when claiming an operation, then finishes bounded in-flight processing and backend cleanup. If it is no longer in Standby, it discards a late scan result/error so the event cannot switch the UI back to Standby. Its existing one-second post-operation pause occurs with RF off. Idle Play, Sync, Stylus, Link/Re-link and unknown modes never initiate a probe; explicitly queued writes retain priority and serialization.

## Risks / Trade-offs

- Physical bus calls can outlast Python deadlines if the kernel/adapter stalls → cap all controllable waits and surface transport failure.
- RF-off can fail on disconnected hardware → report it rather than claiming absence/success, retain original exception context, always close connections.
- RF cycling may expose module/card-specific timing → check normal scanning and linking after deployment on the Pi.
- A mode transition can race an already claimed read → allow that bounded operation to finish and clean up; prevent subsequent standby operations.

## Migration Plan

Run focused and complete Python suites, API/UI regressions, and strict OpenSpec validation. Leave the implementation ready for review and deployment. After deploying through the normal user workflow, check scanning, Link/Re-link, and mode changes in the app using existing tags. This manual end-to-end smoke check is a deployment follow-up, not an implementation gate. Roll back code if detection reliability regresses.

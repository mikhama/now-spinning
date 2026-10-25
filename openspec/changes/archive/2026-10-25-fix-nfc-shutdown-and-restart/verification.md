## Local validation

Date: 2026-10-25. Platform: macOS. Python: 3.14.6. NFC hardware was simulated. No Pi was accessed or deployed from this session.

| Check | Command | Result |
| --- | --- | --- |
| Full Python suite | `/private/tmp/now-spinning-stylus-py314/bin/python -m pytest -q` | 194 tests and 212 subtests passed in 15.78 seconds |
| JavaScript tests | `node --test tests/ui_app_*.test.js` | 33 tests passed |
| OpenSpec change | `openspec validate fix-nfc-shutdown-and-restart --strict` | Passed |
| Whitespace | `git diff --check` | Passed |

The system `python3` is version 3.9.6 and has no pytest package. The tests used the existing temporary Python environment shown above. An initial full-suite run was stopped because the previous worker timing test replaced the removed sleep callback. The test now checks the interruptible event wait and transport close. The complete suite then passed.

## Local evidence

| Requirement | Evidence |
| --- | --- |
| Close only an existing reader; repeated close is safe | `tests/test_nfc.py` checks cleanup before initialization and repeated cleanup after success or RF-off failure. It verifies that driver close still closes the transport. |
| Boardless cleanup has no hardware or input effects | Library and application tests check that cleanup does not initialize hardware or request input. |
| Worker stop is terminal | `tests/test_nfc_coordinator.py` checks mode and write rejection, queued-write removal, active-read completion, and retention of the last record after a read error. |
| Idle pause is interruptible | The idle test stops a worker during a 60-second pause and verifies prompt worker exit and close in that worker. |
| Active write retains completion behavior | The write test stops the worker during a write. The confirmed write persists its record and emits `link_success` before close. The queued second write does not start. |
| Existing NFC timing and formats stay in effect | `tests/test_pn532.py` checks both transports, deadlines, RF timing, payload transfer, and the 500 ms worker pause. `tests/test_nfc.py` checks exact record text. Driver and hardware configuration files were not changed. |
| Common application cleanup | `tests/test_nfc_shutdown.py` checks server return, startup failure, failed worker start, signals, registered exit cleanup, repeated calls, and stylus persistence. |
| Five-second limit and no competing command | A blocked-read test measures the five-second wait and verifies that no queued write or reader close starts while the read remains active. A blocked-close test checks that close is not repeated. |
| Normal process termination during Standby read | Child-process tests send SIGTERM during a real backend read with simulated hardware. Both tag-present and tag-absent cases complete read cleanup, reader RF-off, transport close, and stylus flush before normal process exit. Repeated SIGTERM and SIGINT do not interrupt cleanup. |
| Process-exit hook waits for cleanup | A child process returns with an active daemon worker. The registered exit hook waits for RF-off and transport close. |
| Blocked worker permits process exit | A child process with a blocked read exits normally after five seconds, logs incomplete cleanup, and starts no second hardware command. |
| NFC requests during shutdown return JSON 503 | Endpoint tests cover stopped workers and requests that race with stop. |
| Errors retain diagnostic details | Coordinator tests inspect the logged exception chain for the original error and errno. Driver tests cover command-write, ready-status, ACK, and response failure stages. The diagnostic tests check actual error messages for errno 5, 110, and 121. |
| Stylus checks and Exit response remain in effect | Power and linking API tests verify persisted hours, aborted actions after persistence failure, the existing Exit JSON response, and delayed runner termination. |

## Pi validation

Status: **Pending. The reported I2C restart fault is not verified as fixed.** Local tests confirm the shutdown behavior with simulated hardware. They do not identify the cause of the hardware failure.

The user will deploy and check the application. The user declined the ten-run reporting procedure and said that Codex does not need to check the deployment procedure. No further deployment work is required from Codex. The two reported sequences remain useful for the user's check, including exits with a tag present and absent.

| Sequence | Pi result |
| --- | --- |
| Scan → play → stop → Standby → Exit → reopen | Not checked in this session |
| Scan 1 → 43 → 15 → 23 → 1 → Exit → reopen | Not checked in this session |

If a fault returns, the diagnostic logs identify `NFC read failed`, `NFC write failed`, `NFC reader cleanup failed`, and `NFC shutdown incomplete` separately. Exception tracebacks include errno and transport stage. A successful normal exit reports reader cleanup success before process exit. A timeout reports incomplete cleanup.

The change remains open. Main specifications, README content, and the separate stylus-hours change were not changed.

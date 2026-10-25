## Host verification — 2026-10-24

Host checks pass. The user confirmed that the app is working on the Pi after a full power disconnect, then requested reducing the RF-off pause from one second to 500 ms. Coordinator and between-probe pauses now use 500 ms; detection remains capped at 200 ms. Python 3.14 was used; the system
`python3` is 3.9 and cannot import the pre-existing union type annotations.

| Check | Result |
| --- | --- |
| Original NFC baseline before implementation | 17 tests passed |
| `python3.14 -m unittest discover -s tests -p 'test_nfc*.py'` | 25 tests passed |
| `python3.14 -m unittest discover -s tests -p 'test_pn532.py'` | 28 tests passed |
| Complete Python suite, including API checks (command below) | 143 tests passed |
| `node --test tests/*.test.js` | 21 tests passed |
| `openspec validate duty-cycle-nfc-rf-field --strict --no-interactive` | Passed before implementation and after final code changes |
| `git diff --check` | Passed |
| Existing `keep-last-record-on-nfc-read-error` change | Unchanged; remains separate and unarchived |

Complete suite command (dependencies isolated in a temporary uv cache/environment):

```sh
UV_CACHE_DIR=/private/tmp/now-spinning-uv-cache uv run --offline \
  --python /opt/homebrew/bin/python3.14 \
  --with 'flask~=3.1' --with 'flask-sock~=0.7' --with 'pydantic~=2.13' \
  python -m unittest discover -s tests -p 'test_*.py'
```

The suite's expected mocked Pi-temperature failure logs `missing`; the suite
finishes successfully.

## Requirement evidence

| Requirement | Evidence |
| --- | --- |
| Matching RF controls, one passive attempt, initialization off, close despite RF cleanup error | Both real transport classes exercised by `test_initialization_and_explicit_rf_command_bytes`, `test_initialization_failure_attempts_rf_off_and_closes`, `test_transport_errors_are_nfc_errors_and_cleanup_closes` |
| 200 ms maximum, remaining caller budget, shared monotonic ACK/response deadline | `test_ack_and_response_share_budget`, `test_caller_timeout_caps_budget`, `test_probe_budget_includes_time_spent_enabling_rf`, `test_slow_status_check_cannot_start_more_io_or_sleep_after_deadline`; all driver tests reject use of wall-clock time |
| Continue after UART ACK, fragmented response, empty configuration success, stale/malformed rejection | `test_delayed_response_after_ack_and_fragmented_uart_reply`, `test_stale_responses_are_rejected_before_and_after_ack`, `test_malformed_frames_are_errors` |
| Only valid zero-target replies mean absence; failed RF and transport commands are errors | `test_zero_targets_is_absence_but_malformed_targets_are_errors`, `test_missing_ack_or_response_is_not_absence`, RF-on/transport failure tests |
| Complete multi-page/block transfers retain RF through authentication and payload | Multi-page/block read/write tests in `test_nfc.py`; wire-level write assertions in `test_pn532.py` |
| Finally cleanup after success, no-card timeout, authentication/transfer failure, and interruption; explicit RF-off failures preserve original context | Backend cleanup matrix and context tests in `test_nfc.py`; driver cleanup context test in `test_pn532.py` |
| 500 ms RF-off pauses between probes and after operations, 30-second write wait | `test_no_card_waits_have_half_second_rf_off_pauses`, `test_write_keeps_30_second_detection_limit_and_off_pauses`, `test_worker_sleeps_half_second_with_rf_off_after_each_outcome` |
| Idle Play/Sync/Stylus/Link/Re-link/unknown modes off; transitions out of Standby including active success/absence/failure | Both-transport integration tests `test_inactive_modes_stay_off_after_standby_and_during_idle`, `test_transition_during_probe_cleans_up_without_mode_handler_commands`; late results cannot emit a scan returning the UI to Standby |
| Link/Re-link require requested write, serialized with in-flight reads | `test_link_writes_require_request_and_keep_rf_through_every_page`, threaded coordinator serialization regression |
| Signatures, payloads, boardless behavior, event formats, replacement, duplicate suppression and last-record preservation | Original NFC regressions retained, new boardless regression, complete API suite and all 21 UI tests |
| Timing defaults and cleanup behavior documented | Change design; added README verification block removed as requested |

## Startup regression fix

The startup investigation found an I2C regression: the driver requested a
64-byte response buffer while receiving a six-byte ACK. It now reads the ACK
separately, matching the earlier working driver. The fake I2C transport now
rejects oversized ACK reads and truncates short reads instead of supplying an
entire frame regardless of the request length.

`test_i2c_startup_reads_ack_separately` reproduced a transport timeout followed by
RF-off cleanup failure before the fix and passes afterward. The new startup
error regression also verifies that the original failure remains visible when
cleanup fails, and that the transport still closes.

An initial Pi traceback failed in the first command write. The later bus
diagnostic successfully opened bus 6, received an ACK at address `0x24`, and
sent SAMConfiguration, then failed with `OSError(5)` on a ready-status poll.
That diagnostic used the deployed driver before the polling retry correction.
The SAM frame is unchanged (`00 00 ff 05 fb d4 14 01 14 01 02 00`).

Restored bounded polling retries match the previous working driver's behavior.
Tests now inject both `OSError(5)` and `OSError(110)` before ACK and response
readiness, then complete initialization, firmware retrieval, and RF-off close.
Persistent errors still fail within the shared deadline and retain their errno.
Command writes and frame reads report their stage without blind retries.
Valid busy (`RDY=0`) frame replies also resume polling instead of raising a
malformed-status error. Tests cover recovery through startup/firmware/close
and persistent busy replies exhausting the original shared deadline.

The next deployed traceback includes the polling correction and still fails
on the first SAM command write with `OSError(5)`. This is not resolved by the
polling corrections. Bus, address, initial delay, and SAM command bytes match
the pre-change driver. The old constructor continued after setup write errors;
the new constructor fails immediately.

The user ran the pre-change driver from commit `dabfb02` in the app's virtual
environment on the same Pi. It returned `BASELINE FIRMWARE: None`. Therefore
the current communication failure also affects the old driver; a firmware
response was recovered by changing driver code alone. After fully powering the
Pi/reader off and on, the user reran the current diagnostic and reported:

```text
[1] /dev/i2c-6 opened OK
[2] Device ACKed at 0x24  OK
[3] GetFirmwareVersion via driver...
  FOUND PN532 firmware 1.6
```

This confirms recovery and successful initialization/firmware communication on
the Pi after a full power reset. The initiating cause of the stuck state is not
proven. Kiosk scanning, linking, and mode changes remain the normal next
end-to-end checks; no measuring equipment is needed.

## After deployment: simple end-to-end check

Use the app and existing tags:

1. In Standby, scan a linked record, replace it with another, then remove the tag.
   The correct record should appear and remain selected after removal.
2. Use Link and Re-link to write a tag, then scan it in Standby to confirm the
   selected record opens. Also try a write without presenting a tag: it should
   time out after about 30 seconds without hanging the app.
3. Enter Play, Sync, Stylus, and idle Link/Re-link. Present a different tag;
   Standby scans should not change the selected mode or record.
4. Return to Standby and confirm scanning resumes. Repeat a mode change while
   presenting a tag to check that the app stays responsive.

This manual deployment follow-up has not been run from this workspace. It does
not block implementation. No oscilloscope, RF traces, or temperature/current
measurements are required. The change remains unarchived for review.

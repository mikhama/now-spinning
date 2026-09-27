## 1. NFC Polling

- [x] 1.1 Make the NFC coordinator emit one startup read error before the first successful tag ID, then retain duplicate suppression and the last successful ID through later failures.
- [x] 1.2 Cover startup error/no-card/recovery and failures after a successful scan in coordinator checks.

## 2. Reconnect State

- [x] 2.1 Keep the server's last successful scan or current-record snapshot when a later external null scan is broadcast.
- [x] 2.2 Cover initial startup error and post-success reconnect snapshots in API checks.

## 3. Display State

- [x] 3.1 Handle a startup null scan once and preserve Standby or Playing state on later externally supplied null scans, including after unknown or unlinked IDs.
- [x] 3.2 Cover startup error recovery, retained Standby/Playing record display, and retained Record Not Found view in UI checks.

## 4. Verification

- [x] 4.1 Validate the OpenSpec change and run the relevant NFC coordinator, API, and UI checks.

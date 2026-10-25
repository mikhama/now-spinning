## 1. Storage and tracking

- [x] 1.1 Add additive history schema, local-record lookup, atomic batch save, existing-only report and clear operations; verify preservation, constraints, sync, and rollback.
- [x] 1.2 Implement independent history counter tracking, segment starts/boundaries, ordered pending saves, and commit-aware retries.

## 2. Application coordination

- [x] 2.1 Coordinate both trackers under the playback lock, periodic/no-stylus checkpoints, stop, and stopped selection; preserve history through stylus reset.
- [x] 2.2 Save both kinds of usage on Exit, Shut Down, and cleanup; abort requested actions on either failure and support safe cleanup retries.

## 3. Console and documentation

- [x] 3.1 Add executable standard-library report with chronological grouping, local timezone offsets, full durations, aligned Unicode metadata, and missing-metadata retention.
- [x] 3.2 Add exactly confirmed atomic offline clear, cancellation/error handling, command help, and README instructions.

## 4. Validation

- [x] 4.1 Test tracking/checkpoint behavior, short sessions, stop/resume, record changes, counter resets, empty/unresolved IDs, no stylus, write failures, retries, reset, repeated cleanup, and cancelled exits without lost or duplicated seconds.
- [x] 4.2 Test report totals of 1,234 and 245 seconds, gaps, A → B → A, ties, timezones, Unicode, missing metadata, exact confirmation, cancellation, rollback, missing DB/schema, and preservation of other tables.
- [x] 4.3 Run Python regressions and strict OpenSpec validation; record verification and mark completed tasks, leaving the change open without spec sync or archive.

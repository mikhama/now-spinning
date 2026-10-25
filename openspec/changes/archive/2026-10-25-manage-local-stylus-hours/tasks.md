## 1. Shared database operations

- [x] 1.1 Add existing-only connections and a validated transactional absolute-total operation; delegate reset while preserving its boolean API result.
- [x] 1.2 Ignore remote stylus hours, inserting new styli at zero and preserving all existing local totals.

## 2. Offline commands and instructions

- [x] 2.1 Add executable list/set/reset commands with standard-library-only imports, previous/new output, existing-database behavior, and nonzero error statuses.
- [x] 2.2 Document commands, stopped-app/no-lock procedure, local ownership of hours, and first setup on a new Pi.

## 3. Verification

- [x] 3.1 Test exact set/reset persistence, unchanged metadata/other styli, invalid input, missing resources, rollback and command failure reporting using disposable databases.
- [x] 3.2 Verify a fresh app/tracker loads the saved value and collection sync preserves set, reset, accrued, and legacy local totals with remote hours present or removed.
- [x] 3.3 Run relevant regression tests and OpenSpec validation; record verification evidence and leave this change active without spec sync or archive.

## 1. Recovery Regression Coverage

- [x] 1.1 Add a coordinator test for `same record -> read error -> no card -> same record -> same record` that expects `record -> null -> record` broadcasts and renewed duplicate suppression.

## 2. Coordinator Recovery State

- [x] 2.1 Invalidate the remembered emitted record when broadcasting an NFC read error without clearing the last successfully scanned record.

## 3. Verification

- [x] 3.1 Run the NFC coordinator and NFC library unit tests and confirm all recovery, duplicate-suppression, no-card, and read-error behavior passes.

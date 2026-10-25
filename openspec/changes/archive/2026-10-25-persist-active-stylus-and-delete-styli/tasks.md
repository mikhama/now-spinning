## 1. Database selection and deletion

- [x] 1.1 Normalize legacy active flags, expose boolean flags in stable ID order, and preserve selection and totals during sync.
- [x] 1.2 Add transactional activation and existing-database guarded deletion with commit-before-success behavior.

## 2. Backend tracking and API

- [x] 2.1 Serialize playback transitions, flushes, and stopped selection under the tracker lock; preserve no-op and failure semantics.
- [x] 2.2 Add JSON activation responses and active flags to model/mock data; coordinate reset persistence with tracking.

## 3. UI controls

- [x] 3.1 Initialize from saved selection, connect wraparound navigation, and update both wear bars after success.
- [x] 3.2 Guard controls across modes and hashes, disable Reset during activation, and implement accessible errors and uncertain-result recovery.

## 4. CLI and documentation

- [x] 4.1 Implement standard-library-only delete, active identification in list, and command help.
- [x] 4.2 Document persisted selection, deletion examples, stopped-app procedure, and reimport behavior; remove the selection TODO.

## 5. Verification

- [x] 5.1 Test legacy flags, sync preservation, activation transactions, restart and exclusive accrual, playback rejection, races, missing/repeated activation, and persistence failures.
- [x] 5.2 Test navigation wraparound, both bars, modes/hashes, pending requests, failures, and recovery.
- [x] 5.3 Test inactive/active/missing deletion, missing database, write and commit rollback, and CLI execution without site packages.
- [x] 5.4 Run relevant Python tests, the JavaScript suite, rendered UI checks, and strict OpenSpec validation; record evidence and leave the change open.

## 6. Simplify the stylus error state

- [x] 6.1 Replace the error banner and Retry button with a generic error in the existing empty-state layout; let Prev/Next retry, reloading uncertain saved selection before navigating.
- [x] 6.2 Update JavaScript/browser coverage and change documentation, validate the behavior, and show the revised error state in Playwright.

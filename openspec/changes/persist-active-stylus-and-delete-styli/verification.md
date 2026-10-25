## Results

- Full Python suite with Python 3.14.6: **215 passed, 229 subtests passed**.
- JavaScript suite (`node --test tests/*.test.js`): **47 passed**.
- `openspec validate persist-active-stylus-and-delete-styli --strict`: **valid**.
- `git diff --check`: **clean**.
- Playwright checks against a localhost boardless server with a temporary database: **passed**, with no page errors. The existing design was preserved. The generic error replaces the stylus details in the existing empty-state layout, stays centered at 800×480, in a wider viewport, and at a scaled 420×252 display, and offers Prev/Next to retry.

## Requirement audit

| Requirement | Evidence |
| --- | --- |
| Proposal, design, tasks, and five delta specs | All artifacts are present in this change; strict OpenSpec validation passes. |
| One saved active stylus; legacy first-active/first-ID fallback; preserve metadata and hours | `test_legacy_normalization_preserves_first_active_id_hours_and_metadata`, including multiple flags, no flags, NULL flags, text-ID ordering, and repeated initialization. |
| Boolean active flags and stable navigation order | `test_api_flags_are_boolean_and_navigation_order_does_not_follow_selection`; mock list/detail flags and absent persisted targets are also tested. |
| Restart persistence and exclusive accrual | `test_activation_survives_real_process_restart_and_playback_counts_only_selection` starts a fresh process, loads the real app/tracker, plays, stops, and reads all saved totals. |
| Collection sync preserves selection and totals | Database import tests cover new lower IDs, remote active flags/hours, metadata preservation, first sync, and deleted-row reimport at zero. The actual `/sync` integration test checks that a non-first active ID and all totals survive two syncs. |
| Activation success, 404, 409, and 500 | Real Flask client tests verify JSON status responses and durable selection. Trigger and denied-COMMIT tests prove rollback. |
| Playback rejection changes no tracking state | Rejection tests compare rows, active ID, runtime hours, pending seconds, elapsed baseline, and runtime event state for active, inactive, and missing target IDs during playback. |
| Playback/activation serialization | Thread-controlled tests exercise both orderings. A second thread cannot acquire the tracker lock while activation persistence is paused; a playback transition that wins causes 409. |
| Flush before switch; save failure aborts; same selection is a no-op | Tests cover failed stop flushes, returned-false and raised save failures, flush-before-selection ordering, loading the new saved total, clearing the elapsed baseline, and repeated activation without flushing or writing selection. A selection-write failure after a successful flush is retried without losing or duplicating usage. |
| Persisted Prev/Next with wraparound and both wear bars | JavaScript tests verify initial flags, stable IDs, both directions and boundaries, capacities/colors, active and inactive live-hour events; Playwright verifies persisted IDs and reload behavior with real requests. |
| Playback guards independent of mode/hash | JavaScript tests exercise every mode with normal routing and several debug hashes. Playwright verifies hash transitions and a direct API request during playback. |
| Pending controls, accessible errors, uncertain-result recovery | Tests verify disabled Prev/Next/Reset during requests, duplicate suppression, HTTP errors, lost response, invalid JSON/acknowledgement, initial load failure, repeated reload failure, and stale reads. A generic `role=alert` message replaces stylus details and Reset is hidden; no banner or Retry button remains. Prev/Next retry immediately for confirmed selection, or reload uncertain saved selection before choosing the adjacent ID. Playback beginning during recovery prevents activation. Playwright verifies both lost acknowledgement recovery and failed recovery followed by one Prev click. |
| Safe offline deletion | CLI subprocess tests cover inactive deletion, active `ValueError` and stderr failure, missing IDs/database/schema, SQL-like IDs, rejected writes and commits, rollback, and success only after commit. SQL tracing proves selection check and deletion share one existing-database `BEGIN IMMEDIATE` transaction. |
| Standard-library-only CLI and help | Commands including delete run with `python -S` in a disposable project without the app/dependencies. Help for every command includes the stopped-app procedure and local deletion/reimport behavior. List identifies the active entry. |
| README and completed TODO | README includes persisted selection, playback guards, deletion examples, normal Exit/wait/list/delete/restart steps, and reimport at zero hours. The completed selection TODO is removed. |
| Existing schema, design, and event format | No schema columns were added; existing controls, fonts, palette, and wear bars are reused. Tracker event assertions retain `stylus_hours` with `stylus_id` and `hours`. |
| Change stays open | Main specs and archive directories have no changes. This change remains in `openspec/changes/persist-active-stylus-and-delete-styli`; no sync or archive command was run. |

## Commands and environment

The full passing Python run used `/private/tmp/now-spinning-stylus-py314/bin/python -m pytest -q --tb=short`. The focused application/CLI tests also passed under Python 3.11.15. The broader suite under Python 3.11 has an existing PN532 test-module/mock import problem; the same failures were reproduced from an untouched `git archive HEAD` checkout. Python 3.14 runs the entire suite successfully.

The browser test is `tests/stylus_selection.browser.js`, run using the Playwright CLI against a disposable server with at least two saved styli. It uses synthetic playback events, intercepts activation failures, and restores the initial selection. No real collection database or hardware was used.

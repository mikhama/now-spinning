## Verification: add-playback-session-history

Verified locally on 2026-10-25. The change remains in `openspec/changes/add-playback-session-history`; main specifications were not synced and the change was not archived.

| Dimension | Result |
| --- | --- |
| Completeness | 9/9 tasks implemented; all proposal artifacts and 10 delta requirements reviewed |
| Correctness | All 10 requirements and 16 scenarios have implementation and passing test evidence |
| Coherence | Additive SQLite storage, separate tracking under the playback lock, independent saves, existing-only tools, and documented offline clear follow the design |

## Executed checks

| Check | Command | Result |
| --- | --- | --- |
| Full Python regressions | `/private/tmp/now-spinning-stylus-py314/bin/python -m unittest discover -s tests -p 'test_*.py'` | 257 tests passed on Python 3.14.6; log: `/private/tmp/now-spinning-sessions-unittest.log` |
| New storage, tracker, API, and console tests | `/private/tmp/now-spinning-power-venv/bin/python -m pytest -q tests/test_session_history.py tests/test_session_history_api.py tests/test_sessions_history_cli.py` | 42 tests and 11 subtests passed on Python 3.11.15 |
| Python 3.11 regressions excluding known driver harness problem | `/private/tmp/now-spinning-power-venv/bin/python -m pytest -q tests --ignore=tests/test_pn532.py --tb=short` | 229 tests and 117 subtests passed |
| Strict change validation | `openspec validate add-playback-session-history --strict` | Passed |
| Whitespace validation | `git diff --check` | Passed |
| Executable and help | Real executable invoked from `/private/tmp`, with both `--help` forms | Passed in console tests |
| Standard-library-only operation | Executable run through `runpy` with Python `-S`, using an isolated test database | Report, cancelled clear, and confirmed clear passed without site packages |

The initial Python 3.11/pytest full run exposed the existing PN532 test harness's module-mocking problem (`SMBus`/`i2c_msg` left as `None`). The unchanged `HEAD` exported to `/private/tmp/now-spinning-sessions-baseline-14u4xb4y` reproduced the identical 67 failed checks, 24 passes, and 60 passed subtests for `tests/test_pn532.py`. Its baseline output is in `/private/tmp/now-spinning-sessions-baseline.log`. The full Python 3.14 unittest run, including all PN532 tests, passes. No driver changes were needed.

## Requirement and scenario evidence

| Requirement and covered scenarios | Implementation | Passing evidence |
| --- | --- | --- |
| Manual DB deletion for schema changes: database init preserves existing data | `api/services/db/database.py:22` | `test_additive_initialization_and_sync_preserve_all_existing_data` verifies the revised migration requirement: normal initialization adds the table while retaining the existing database and its records, stylus totals, and committed history. |
| Additive playback history storage: upgrade existing database; invalid duration | `api/services/db/database.py:48`, `api/session_history.py:15` | `test_additive_initialization_and_sync_preserve_all_existing_data` compares legacy records, totals, and sync status before/after repeated initialization, then verifies history through collection upserts. `test_schema_rejects_empty_record_and_nonpositive_or_fractional_durations` verifies constraints. Tracker tests assert exact `+00:00` timestamps. |
| Atomic history persistence and deletion: commit fails | `api/services/db/database.py:303`, `api/services/db/database.py:334` | `test_failed_batch_rolls_back_earlier_rows_and_retry_saves_once` rejects a later insert and proves rollback of earlier rows. `test_commit_failure_rolls_back_inserts_and_clear` denies COMMIT and checks unchanged saved history. |
| Count only identified local-record playback: identify after unknown; no stylus | `api/session_history.py:44`, `api/main.py:254` | `test_empty_unresolved_and_later_resolved_records_never_back_count`, `test_local_record_lookup_requires_existing_nonempty_id`, `test_unknown_playback_adds_no_rows_or_separator`, and `test_history_checkpoints_without_any_stylus` verify local lookup, skipped unknowns, fresh resolution baselines, and counted history without creating styli. |
| Segment boundaries and timestamps: checkpoint followed by stop; change and counter reset | `api/session_history.py:38`, `api/session_history.py:70`, `api/session_history.py:83` | `test_first_counted_interval_and_checkpoint_advance_the_start` checks first-interval start and exact saved-duration advancement even with delayed observation. `test_short_session_stop_resume_excludes_the_gap`, `test_record_change_closes_previous_before_new_counter_baseline`, and `test_counter_reset_closes_previous_and_starts_a_new_segment` cover boundaries. API tests verify the committed rows. |
| Ordered retryable checkpoints: failure spans multiple records | `api/session_history.py:83`, `api/main.py:266`, `api/main.py:429` | `test_failures_keep_multiple_segments_in_order_until_commit_then_retry_is_empty` checks failed A → B → A batches and a single successful retry. API tests cover periodic saves, short stops, no-stylus checkpoints, a stylus checkpoint with less than 600 history seconds, failed stopped selection, both power paths, and repeated cleanup. |
| Independent save attempts and shutdown guard: one save fails; stylus reset | `api/main.py:553`, `api/main.py:571`, `api/main.py:401` | API tests cover a history exception with successful stylus save, periodic failures on either side, simultaneous save exceptions, both cancelled power actions, successful retries, and retained pending history/baseline through stylus reset. `test_repeated_cleanup_retries_pending_history_once_and_freezes_counting` proves no additional seconds or duplicate writes during cleanup. |
| One committed-history console report: summed example with gaps; return to previous album | `api/services/db/database.py:318`, `api/sessions_history_cli.py:22` | `test_example_totals_are_1234_and_245_seconds_despite_large_gaps` checks totals and first start. `test_a_b_a_remains_three_rows_in_chronological_then_primary_key_order` checks chronological sorting, primary key ties, adjacent-only grouping, and separate albums sharing an artist. `test_report_reads_only_committed_rows_while_writer_is_open` checks concurrent saved-only reads. |
| Readable local-time report: missing metadata and long duration | `api/sessions_history_cli.py:32`, `api/sessions_history_cli.py:46`, SQLite left join | Console tests verify required aligned columns, 25:01:01 duration, readable Polish/Japanese metadata and combining characters, record metadata deletion without history loss, system timezone conversion, and both offsets during the Warsaw DST transition. |
| Exact confirmed offline clear: confirmation/cancellation; missing database/schema | `api/sessions_history_cli.py:66`, `api/services/db/database.py:334`, `README.md:194` | Console tests accept only `yes I hereby confirm`, reject case/whitespace variations, handle EOF/KeyboardInterrupt, prove failed-commit rollback without a success message, preserve record/stylus/status tables, reject missing DB/schema without creation or migration, and exercise both help forms and actual command execution. |

## Reproducible totals fixture

The attachment gives the target totals without source example rows. The test uses these explicit entries, inserted in reverse chronological order to exercise report sorting:

| Record | UTC start | Recorded seconds |
| --- | --- | --- |
| A | 2026-01-01T10:00:00+00:00 | 600 |
| A | 2026-04-01T10:00:00+00:00 | 600 |
| A | 2026-10-01T10:00:00+00:00 | 34 |
| B | 2026-10-02T10:00:00+00:00 | 120 |
| B | 2026-10-24T10:00:00+00:00 | 125 |

The report gives A **00:20:34** (1,234 seconds) and B **00:04:05** (245 seconds). Gaps add no duration.

## Assessment

No outstanding critical issues, warnings, or suggestions for this change. Existing standalone stylus behavior and application regressions pass. Validation used isolated test databases and simulated hardware; no Pi deployment was requested or performed. Abrupt power loss can still lose uncommitted seconds, as documented. Record changes establish a new counter baseline so ambiguous intervals and earlier unknown playback are not assigned retroactively.

All requested implementation and local validation work is complete. Leave this change open; do not sync or archive it.

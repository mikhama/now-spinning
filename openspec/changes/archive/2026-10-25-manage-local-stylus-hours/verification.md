## Verification results

Verified on 2026-10-25 with disposable databases and a local collection fixture. The developer's project database was not changed. Application tests used Python 3.14 in a temporary virtual environment; standalone CLI tests also passed with system Python 3.9 and with site packages disabled.

```bash
python3 -m unittest discover -s tests -p test_stylus_hours_cli.py -v
# 16 tests passed

/private/tmp/now-spinning-stylus-py314/bin/python -m pytest -q \
  tests/test_stylus_hours_cli.py tests/test_stylus_hours.py \
  tests/test_linking_api.py tests/test_power_api.py
# 85 passed, 62 subtests passed

openspec validate manage-local-stylus-hours --strict
# Change 'manage-local-stylus-hours' is valid

git diff --check
# Passed
```

## Requirement evidence

| Requirement | Evidence |
| --- | --- |
| Executable lists every saved ID, name, and total | CLI subprocess test checks both rows, including a Unicode name, executable permission, and unchanged saved values; empty-table behavior is also tested. |
| Set replaces the total and reports old/new values | Real executable changes `102.4` to `97.3`; a separate connection reads exactly `97.3`; output matches the requested example. Repeated sets, zero, and values with additional decimal places are tested without rounding. |
| Reset saves zero using the shared operation | CLI reset test reads zero from a fresh connection. Shared reset delegates to `set_stylus_hours`, retains boolean results, and existing reset API/runtime tests pass. |
| Other styli and metadata remain unchanged | Set test compares the complete target row excluding its total and the entire other row. |
| Invalid input leaves saved totals unchanged | Negative, nonnumeric, empty, NaN, infinity, overflow, and invalid command arguments fail with unchanged rows; the database operation also validates direct callers. |
| Missing database/stylus fails without creation | All three commands fail without creating a database directory; missing-ID and SQL-like-ID tests preserve all rows. An existing empty database is not initialized. |
| Failed save returns failure without success output | A real SQLite trigger aborts writes in subprocess tests. Denying COMMIT through SQLite's authorizer exercises transaction rollback after the update, with unchanged rows and no success output. |
| App restart loads saved total | After offline set and reset followed by local collection sync, fresh Python processes import the real app and verify both `/styli` and a new playback tracker read the saved total. |
| Collection sync ignores remote hours and preserves local totals | The real `/sync` pipeline reads fixture JSON and updates SQLite, with only git transport mocked. Existing legacy, accrued, set, and reset totals survive sync both before and after remote `distance_hours` removal; new styli start at zero with or without remote hours. |
| Standard-library-only offline tool | Actual script passes list/set/reset under `python -S` in a disposable project containing only the CLI and database modules, without the Flask app or hardware code. |
| Stopped-app/no-lock procedure and new-Pi setup | README and command/subcommand help include normal Exit, waiting for stop, list/set/reset, restart, the pending-usage risk, and sync-before-seeding instructions. Implementation has no process detection, application lock, or process control. |
| Keep OpenSpec change active without syncing or archiving | Proposal, design, delta specs, tasks, and this evidence remain in `openspec/changes/manage-local-stylus-hours/`. Main specs and archived changes are unchanged. |

These checks exercise database persistence and app reload behavior locally. They do not operate or restart a physical Pi, access the collection's remote repository, or change its JSON.

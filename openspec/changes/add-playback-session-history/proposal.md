## Why

Stylus totals retain equipment wear but cannot show which records were played or when. Persisting known-record playback intervals alongside those totals provides a durable listening history without inventing historical playback.

## What Changes

- Add an additive `sessions_log` table and an independent playback history tracker with ordered, retryable saves at the existing usage checkpoints.
- Save history even without a stylus, and require both usage saves to succeed before Exit or Shut Down proceeds.
- Add the standard-library-only `bin/sessions-history` report and exactly confirmed offline clear command, plus help and README instructions.
- Keep this change open after implementation and validation; do not sync specs or archive it.

## Capabilities

### New Capabilities

- `playback-session-history`: Count and persist known-record playback segments independently of stylus availability.
- `sessions-history-cli`: Report consecutive record sessions and clear saved history with exact confirmation.

### Modified Capabilities

- `sync-database`: Initialize the additive history schema while preserving existing collection data, stylus totals, and history through sync.

## Impact

Touches the SQLite layer, playback event coordination, stopped stylus selection, application save/cleanup paths, console tooling, README, and Python regression tests. Adds no dependencies, UI, or HTTP endpoints. Existing pre-feature playback cannot be reconstructed.

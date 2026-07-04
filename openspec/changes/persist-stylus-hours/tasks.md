## 1. Database Persistence

- [x] 1.1 Add an active-stylus lookup helper that returns the selected stylus ID and current `distance_hours`, returning no row when no stylus exists.
- [x] 1.2 Add an additive stylus-hour increment helper that updates `distance_hours = distance_hours + ?`, commits the write, and reports whether a row was updated.
- [x] 1.3 Configure SQLite connections for explicit stylus-hour durability using WAL plus a durable synchronous setting.
- [x] 1.4 Add database tests for active-stylus lookup, existing/missing stylus increments, and committed increments visible from a new connection.

## 2. Stylus Hours Tracker

- [x] 2.1 Create a backend tracker component that resolves the active stylus, tracks current runtime hours, tracks last playback elapsed seconds, and tracks pending unflushed seconds.
- [x] 2.2 Process `status: "play"` events so elapsed playback increments active stylus runtime hours and pending usage without creating rows when no active stylus exists.
- [x] 2.3 Emit or return `stylus_hours` events after playback increments so existing WebSocket clients and initial runtime state receive live hours.
- [x] 2.4 Flush pending usage to SQLite whenever unflushed playback reaches 600 seconds, then clear only the flushed pending usage.
- [x] 2.5 Flush all pending usage when a `status: "stop"` event is processed.
- [x] 2.6 Clear pending usage and runtime hours for a stylus after its reset endpoint successfully persists `distance_hours = 0`.

## 3. API Integration

- [x] 3.1 Integrate the tracker into backend message broadcasting so RPM-derived playback status drives stylus-hour tracking before clients need the updated `stylus_hours` event.
- [x] 3.2 Ensure `build_initial_events()` continues to seed newly connected WebSocket clients with the latest runtime `stylus_hours`.
- [x] 3.3 Flush pending stylus usage synchronously inside enabled `/kiosk/exit` handling before scheduling kiosk runner termination.
- [x] 3.4 Preserve disabled `/kiosk/exit` behavior so rejected requests do not flush pending usage and do not request termination.
- [x] 3.5 Register normal shutdown cleanup for process exit or shutdown signals that attempts to flush pending stylus usage.

## 4. Verification

- [x] 4.1 Add tracker unit tests for active stylus accrual from `00:00` to `10:00`, no-active-stylus skip behavior, live `stylus_hours` event generation, 600-second periodic flush, sub-threshold pending behavior, stop flush, and reset clearing pending usage.
- [x] 4.2 Add API tests proving enabled kiosk exit flushes pending usage before termination and disabled kiosk exit does not flush or terminate.
- [x] 4.3 Add or update integration tests covering WebSocket/runtime state updates for emitted `stylus_hours` during playback.
- [x] 4.4 Run the relevant test suite and OpenSpec validation for `persist-stylus-hours`.

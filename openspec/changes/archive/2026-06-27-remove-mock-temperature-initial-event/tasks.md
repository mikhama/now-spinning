## 1. Backend Temperature Events

- [x] 1.1 Initialize runtime temperature state as unavailable instead of a mocked numeric value.
- [x] 1.2 Factor the sysfs temperature read into a reusable helper that returns Celsius or `None`.
- [x] 1.3 Remove the `GET /temperature` endpoint so temperature is not fetched by the frontend.
- [x] 1.4 Ensure `build_initial_events()` sends a `temperature_c` event with `temp_c: null` before any real reading exists.
- [x] 1.5 Add a backend temperature publisher that reads temperature and broadcasts `temperature_c` events every 30 seconds.
- [x] 1.6 Start the publisher once when the API process runs, avoiding duplicate workers in the same process.

## 2. Frontend Temperature Consumption

- [x] 2.1 Remove frontend-driven temperature polling from app initialization.
- [x] 2.2 Keep WebSocket `temperature_c` handling as the only top-bar temperature update path.
- [x] 2.3 Confirm `temp_c: null` renders as `N/A` and numeric readings render as rounded Celsius.

## 3. Tests

- [x] 3.1 Add backend tests proving initial temperature events use `temp_c: null` and never default to a mock value.
- [x] 3.2 Add backend tests for successful and failed temperature publisher payloads without waiting for the real 30-second interval.
- [x] 3.3 Add or update frontend tests, if available, to cover removal of `/temperature` polling and WebSocket-driven temperature display.
- [x] 3.4 Run the relevant test suite and OpenSpec validation for this change.

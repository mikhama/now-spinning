## Why

The backend currently seeds new WebSocket clients with a mocked board temperature of 59°C, which can display false hardware state. Temperature updates should come from actual backend reads and remain unavailable as `N/A` until a real reading exists.

## What Changes

- Remove the mocked initial `temperature_c: 59` runtime value.
- Send an initial `temperature_c` WebSocket event with `temp_c: null` so the UI shows `N/A`.
- Have the backend read board temperature every 30 seconds and broadcast `temperature_c` events to connected WebSocket clients.
- Remove the `/temperature` endpoint; temperature is delivered to the frontend only through backend WebSocket events.
- Ensure boardless or failed temperature reads broadcast `temp_c: null` rather than any mock value.

## Capabilities

### New Capabilities

### Modified Capabilities
- `api-server`: WebSocket initial state and backend event publishing behavior for temperature events changes.
- `pi-temperature`: Periodic temperature updates are backend-pushed over WebSocket every 30 seconds, with unavailable readings represented as null; the REST temperature endpoint is removed.
- `ui-app`: The UI consumes temperature updates only from WebSocket events.

## Impact

- Affects `api/main.py` runtime state, temperature reading, WebSocket connection flow, periodic broadcast behavior, and removal of the temperature REST route.
- Affects `ui/app.js` initialization by removing frontend temperature fetching.
- Adds or updates tests around initial WebSocket event construction and temperature event publishing.

## 1. Successful NFC Scan Contract

- [x] 1.1 Update coordinator regression tests so an unlinked but successfully read tag emits its real record ID and remains duplicate-suppressed.
- [x] 1.2 Remove the coordinator's linked-record rejection so all successfully decoded IDs follow the normal scan path while real read errors still emit `record_id: null`.

## 2. Standby Record Resolution

- [x] 2.1 Add frontend regression coverage requiring unlinked scan IDs to use the not-found state while null scan IDs retain the NFC-error state.
- [x] 2.2 Make the WebSocket scan handler activate only linked records and route unlinked or unknown IDs to “Record Not Found.”

## 3. Verification

- [x] 3.1 Run the focused NFC coordinator and frontend/API tests.
- [x] 3.2 Run the complete automated test suite and validate the OpenSpec change.

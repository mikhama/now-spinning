## MODIFIED Requirements

### Requirement: Backend main with NFC examples
The NFC demo from `backend/main.py` SHALL be moved to `exp/nfc_test.py`. The `api/main.py` file SHALL serve as the new Flask API server entry point.

#### Scenario: Run NFC demo from new location
- **WHEN** the user runs `python -m exp.nfc_test`
- **THEN** the NFC read/write demo menu SHALL work as before (read tag, write tag, quit)

#### Scenario: Run API server
- **WHEN** the user runs `python -m api.main`
- **THEN** the application SHALL start a Flask HTTP server with REST and WebSocket endpoints

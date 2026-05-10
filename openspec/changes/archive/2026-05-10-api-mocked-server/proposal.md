## Why

The project needs a Flask-based HTTP API with WebSocket support to serve vinyl record and stylus data, replacing the current NFC demo backend. This enables a future UI to display now-playing information, stylus wear tracking, and turntable status in real time. Starting with mocked responses allows frontend development to proceed independently.

## What Changes

- **BREAKING** Rename `backend/` folder to `api/` and update all references (README, imports)
- Move existing `backend/main.py` (NFC demo) to `exp/nfc_test.py` and update README with the new path
- Add `requirements.in` with pinned (`~=`) dependencies (Flask, pydantic, flask-sock, etc.)
- Add README instructions for installing dependencies from `requirements.in`
- Create Flask API server with REST endpoints:
  - `GET /records` — list all records
  - `GET /records/<id>` — get a single record
  - `POST /records/<id>/link` — link a record (returns `{ success: true }`)
  - `POST /records/sync` — sync records (returns `{ success: true }`)
  - `GET /styli` — list all styli
  - `GET /styli/<id>` — get a single stylus
  - `POST /styli/<id>/reset` — reset stylus hours (returns `{ success: true }`)
  - `POST /styli/sync` — sync styli (returns `{ success: true }`)
  - `POST /shutdown` — shut down the server (returns `{ success: true }`)
- Create WebSocket endpoint emitting events on connection:
  - `stylus_hours` — `{ hours: float, stylus_id: str }`
  - `temperature_c` — `{ temp_c: int }`
  - `current_record` — `{ record_id: str }`
  - `status` — `{ status: "idle" | "start" | "play" | "stop" }`
- Define Pydantic models for `Record` (with sides containing tracks), `Side`, `Track`, and `Stylus`
- Mock data: Linkin Park — Papercuts (Discogs release 30348842, master 3453923), Sumiko Olympia stylus at 89.6 hours
- Download cover image to `ui/images/30348842.jpeg`

## Capabilities

### New Capabilities
- `api-server`: Flask API server with REST endpoints, WebSocket events, Pydantic models, and mocked data
- `api-project-setup`: Project restructuring (backend→api rename), requirements.in, README updates

### Modified Capabilities
- `backend-examples`: **BREAKING** — The `backend/` module is being renamed to `api/`, changing the entry point from `python -m backend.main` to `python -m api.main`

## Impact

- `backend/` directory renamed to `api/` — all imports and CLI commands change
- New dependencies: Flask, pydantic, flask-sock (added via `requirements.in`)
- README updated with new install and run instructions
- New `ui/images/` directory for cover art assets
- Existing NFC demo code in `backend/main.py` is preserved as `exp/nfc_test.py`

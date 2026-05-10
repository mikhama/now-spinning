## Context

The project currently has a `backend/` module with a simple NFC demo CLI (`backend/main.py`). The goal is to replace this with a Flask-based HTTP API serving mocked vinyl record and stylus data, enabling future UI development. The API needs both REST endpoints and WebSocket support for real-time turntable status updates.

Current state:
- `backend/main.py` — NFC read/write demo menu (to be moved to `exp/nfc_test.py`)
- `lib/nfc.py` — NFC library (untouched by this change)
- No dependency management beyond the venv itself

## Goals / Non-Goals

**Goals:**
- Rename `backend/` to `api/` for clarity
- Establish `requirements.in` with `~=` pinned dependencies
- Create a Flask API server with REST + WebSocket endpoints
- Define Pydantic data models for records and styli
- Return mocked data (Linkin Park Papercuts, Sumiko Olympia stylus)
- Send initial state via WebSocket on connection

**Non-Goals:**
- Real NFC integration or hardware communication
- Database or persistent storage
- Authentication or authorization
- Production deployment configuration
- UI implementation (only the `ui/images/` folder for cover art)

## Decisions

### Flask as the web framework
Flask is lightweight, well-suited for small APIs, and the user explicitly requested it. Alternative: FastAPI would provide async and auto-docs, but Flask was specified.

### flask-sock for WebSocket support
`flask-sock` provides simple WebSocket support built on top of Flask without requiring a separate ASGI server. Alternative: `flask-socketio` offers Socket.IO protocol with rooms/namespaces but adds complexity not needed here. `flask-sock` uses raw WebSocket which is simpler for pushing events.

### Pydantic for data models
User requested Pydantic. Models define `Record` (with nested `Track` list) and `Stylus`. Pydantic provides validation and clean serialization. All mock data is defined as model instances.

### requirements.in for dependency management
Using `requirements.in` with `~=` version specifier (compatible release). This allows patch updates while pinning the minor version. Users install via `pip install -r requirements.in`.

### JSON event protocol for WebSocket
Each WebSocket message is a JSON object with `event` and `data` fields:
```json
{"event": "stylus_hours", "data": {"hours": 89.6, "stylus_id": "1"}}
{"event": "temperature_c", "data": {"temp_c": 59}}
{"event": "current_record", "data": {"record_id": "1"}}
{"event": "status", "data": {"status": "idle"}}
```
All four events are sent immediately after WebSocket connection is established.

### Mock data structure
All mock data lives in a dedicated module (`api/mock_data.py`) with Pydantic model instances. The cover image is downloaded and stored as `ui/images/30348842.jpeg` (named by Discogs release ID).

### Project structure
```
api/
  __init__.py
  main.py          # Flask app, routes, WebSocket, entry point
  models.py         # Pydantic models (Record, Track, Stylus)
  mock_data.py      # Mock data instances
ui/
  images/
    30348842.jpeg   # Papercuts cover art
requirements.in
```

## Risks / Trade-offs

- **flask-sock requires compatible Werkzeug version** → Pin flask-sock and Flask together with `~=` to avoid incompatibility.
- **WebSocket connection is one-directional (server→client push only)** → Sufficient for initial state broadcast; can be extended later if client needs to send commands.
- **Mock data is hardcoded** → Acceptable for development phase; will be replaced with real data sources later.
- **Renaming backend/ to api/ is a breaking change** → All documentation and commands will be updated in the same change to maintain consistency.
- **Existing NFC demo is moved, not deleted** → `backend/main.py` is preserved as `exp/nfc_test.py` and README is updated with the new run command (`python -m exp.nfc_test`).

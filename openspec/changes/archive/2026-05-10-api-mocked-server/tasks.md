## 1. Project Restructuring

- [x] 1.1 Move `backend/main.py` to `exp/nfc_test.py` (preserve the NFC demo)
- [x] 1.2 Rename `backend/` directory to `api/`
- [x] 1.3 Update `README.md` — replace all `backend` references with `api`, add `python -m exp.nfc_test` for NFC demo
- [x] 1.4 Update any existing specs referencing `backend/` (e.g., `openspec/specs/backend-examples/spec.md`)

## 2. Dependency Management

- [x] 2.1 Create virtual environment (`python -m venv env`) and activate it
- [x] 2.2 Create `requirements.in` with Flask, flask-sock, and pydantic (all pinned with `~=`)
- [x] 2.3 Install dependencies: `pip install -r requirements.in`
- [x] 2.4 Add README section explaining how to install dependencies from `requirements.in`

## 3. Pydantic Models

- [x] 3.1 Create `api/models.py` with `Track` model (title, artist, duration, linked)
- [x] 3.2 Add `Record` model (id, release_id, master_id, title, artist, cover_image, tracks)
- [x] 3.3 Add `Stylus` model (id, name, hours)

## 4. Mock Data

- [x] 4.1 Create `api/mock_data.py` with Linkin Park Papercuts record (id "1", release_id "30348842", master_id "3453923", 20 tracks from Discogs)
- [x] 4.2 Add Sumiko Olympia stylus mock data (id "1", name "Sumiko Olympia", hours 89.6)
- [x] 4.3 Download Papercuts cover image from Discogs and save to `ui/images/30348842.jpeg`

## 5. Flask API Server

- [x] 5.1 Create `api/__init__.py` (update existing)
- [x] 5.2 Create `api/main.py` with Flask app initialization
- [x] 5.3 Add `GET /records` endpoint — returns list of all records
- [x] 5.4 Add `GET /records/<id>` endpoint — returns single record or 404
- [x] 5.5 Add `POST /records/<id>/link` endpoint — returns `{ "success": true }`
- [x] 5.6 Add `POST /records/sync` endpoint — returns `{ "success": true }`
- [x] 5.7 Add `GET /styli` endpoint — returns list of all styli
- [x] 5.8 Add `GET /styli/<id>` endpoint — returns single stylus or 404
- [x] 5.9 Add `POST /styli/<id>/reset` endpoint — returns `{ "success": true }`
- [x] 5.10 Add `POST /styli/sync` endpoint — returns `{ "success": true }`
- [x] 5.11 Add `POST /shutdown` endpoint — returns `{ "success": true }`

## 6. WebSocket Support

- [x] 6.1 Add WebSocket endpoint using flask-sock
- [x] 6.2 On connection, send initial events: stylus_hours (89.6, stylus_id "1"), temperature_c (59), current_record ("1"), status ("idle")
- [x] 6.3 Each event sent as JSON with `event` and `data` fields

## 7. Finalize

- [x] 7.1 Add `if __name__` block to `api/main.py` for running the server
- [x] 7.2 Verify server starts with `python -m api.main`
- [x] 7.3 Update README with final usage instructions

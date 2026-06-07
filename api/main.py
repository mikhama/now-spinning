import json
import os

from flask import Flask, Response, jsonify, request
from flask_sock import Sock

from api.mock_data import RECORDS, STYLI

app = Flask(__name__, static_folder="../ui", static_url_path="")
sock = Sock(app)

# Connected WebSocket clients for event broadcasting
connected_clients: set = set()

# Runtime event state used to seed newly connected clients without fabricating
# a default record.
runtime_state = {
    "stylus_hours": {"1": 89.6},
    "temperature_c": 59,
    "current_record_id": None,
    "last_scan_data": None,
    "status": "idle",
    "status_time": None,
}


def update_runtime_state(message):
    event = message.get("event")
    data = message.get("data") or {}

    if event == "stylus_hours":
        stylus_id = data.get("stylus_id")
        hours = data.get("hours")
        if stylus_id is not None and hours is not None:
            runtime_state["stylus_hours"][str(stylus_id)] = hours
    elif event == "temperature_c":
        temp_c = data.get("temp_c")
        if temp_c is not None:
            runtime_state["temperature_c"] = temp_c
    elif event == "current_record":
        runtime_state["current_record_id"] = data.get("record_id")
        runtime_state["last_scan_data"] = None
    elif event == "scan":
        runtime_state["last_scan_data"] = data
        runtime_state["current_record_id"] = data.get("record_id")
    elif event == "status":
        status = data.get("status")
        if status is not None:
            runtime_state["status"] = status
            runtime_state["status_time"] = data.get("time") if status == "play" else None


def build_initial_events():
    events = []

    for stylus_id, hours in runtime_state["stylus_hours"].items():
        events.append({"event": "stylus_hours", "data": {"hours": hours, "stylus_id": stylus_id}})

    temperature_c = runtime_state.get("temperature_c")
    if temperature_c is not None:
        events.append({"event": "temperature_c", "data": {"temp_c": temperature_c}})

    if runtime_state["last_scan_data"] is not None:
        events.append({"event": "scan", "data": runtime_state["last_scan_data"]})
    elif runtime_state["current_record_id"] is not None:
        events.append({"event": "current_record", "data": {"record_id": runtime_state["current_record_id"]}})

    status = runtime_state.get("status")
    if status is not None:
        status_event = {"status": status}
        if runtime_state.get("status_time") is not None:
            status_event["time"] = runtime_state["status_time"]
        events.append({"event": "status", "data": status_event})

    return events


def broadcast_message(message, *, exclude_client=None):
    payload = json.dumps(message)
    update_runtime_state(message)
    for client in list(connected_clients):
        if client is exclude_client:
            continue
        try:
            client.send(payload)
        except Exception:
            connected_clients.discard(client)


@app.route("/")
def index():
    return app.send_static_file("index.html")


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@app.get("/records")
def list_records():
    from api.services.db.database import get_all_records, init_db
    init_db()
    rows = get_all_records()
    records = []
    for row in rows:
        sides = json.loads(row["sides"]) if isinstance(row["sides"], str) else row["sides"]
        records.append({
            "id": row["id"],
            "release_id": row["release_id"],
            "master_id": row["master_id"],
            "title": row["title"],
            "artist": row["artist"],
            "cover_image": "images/albums/" + row["release_id"] + ".jpeg",
            "linked": bool(row["linked"]),
            "sides": sides,
        })
    return jsonify(records)


@app.get("/records/<id>")
def get_record(id):
    record = RECORDS.get(id)
    if record is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(record.model_dump())


@app.post("/records/<id>/link")
def link_record(id):
    from api.services.db.database import init_db, mark_record_linked

    init_db()
    if not mark_record_linked(id):
        return jsonify({"error": "Not found"}), 404
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Styli
# ---------------------------------------------------------------------------

@app.get("/styli")
def list_styli():
    return jsonify([s.model_dump() for s in STYLI.values()])


@app.get("/styli/<id>")
def get_stylus(id):
    stylus = STYLI.get(id)
    if stylus is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(stylus.model_dump())


@app.post("/styli/<id>/reset")
def reset_stylus(id):
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

REPO_URL = "git@github.com:mikhama/my-musical-journey.git"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP_REPO_DIR = os.path.join(PROJECT_ROOT, "tmp", "my-musical-journey")
IMAGES_DEST = os.path.join(PROJECT_ROOT, "ui", "images", "albums")


@app.get("/sync/status")
def sync_status():
    from api.services.db.database import get_last_sync_date, init_db
    init_db()
    last = get_last_sync_date()
    return jsonify({"last_sync": last})


@app.post("/sync")
def sync():
    from api.services.db.database import (
        init_db,
        get_last_sync_date,
        update_sync_date,
        upsert_records,
        upsert_styli,
    )
    from api.services.sync.data_extractor import copy_images, extract_data
    from api.services.sync.git_sync import clone_or_pull

    def generate():
        try:
            init_db()
            last = get_last_sync_date()
            status_text = "Last updated " + (last if last else "never")
            yield "data: " + json.dumps({"status": status_text}) + "\n\n"

            yield "data: " + json.dumps({"status": "Downloading collection"}) + "\n\n"
            clone_or_pull(REPO_URL, TMP_REPO_DIR)
            app.logger.info("Git sync complete: %s", TMP_REPO_DIR)

            yield "data: " + json.dumps({"status": "Updating database"}) + "\n\n"
            styli, records = extract_data(TMP_REPO_DIR)
            app.logger.info("Extracted %d styli, %d records", len(styli), len(records))

            if not records:
                app.logger.warning("No records extracted — check repo structure at %s", TMP_REPO_DIR)
                yield "data: " + json.dumps({"status": "Sync warning: 0 records found"}) + "\n\n"

            upsert_styli(styli)
            upsert_records(records)
            copy_images(TMP_REPO_DIR, IMAGES_DEST)
            update_sync_date()

            yield "data: " + json.dumps({"status": "Sync complete"}) + "\n\n"
        except Exception as e:
            app.logger.error("Sync error: %s", e, exc_info=True)
            yield "data: " + json.dumps({"status": "Sync error"}) + "\n\n"

    return Response(generate(), mimetype="text/event-stream")


# ---------------------------------------------------------------------------
# Temperature
# ---------------------------------------------------------------------------

@app.get("/temperature")
def get_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            millidegrees = int(f.read().strip())
            return jsonify({"celsius": millidegrees / 1000})
    except (FileNotFoundError, IOError, ValueError) as e:
        app.logger.error("Failed to read Pi temperature: %s", e)
        return jsonify({"celsius": None})


# ---------------------------------------------------------------------------
# Server control
# ---------------------------------------------------------------------------

@app.post("/shutdown")
def shutdown():
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Events (boardless mode event publishing)
# ---------------------------------------------------------------------------

@app.post("/events")
def post_event():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid JSON"}), 400

    event = data.get("event")
    event_data = data.get("data") or {}

    if event == "link_success":
        record_id = event_data.get("record_id")
        if not record_id:
            return jsonify({"error": "Missing record_id"}), 400

        from api.services.db.database import init_db, mark_record_linked

        init_db()
        if not mark_record_linked(record_id):
            return jsonify({"error": "Not found"}), 404

    broadcast_message(data)
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@sock.route("/ws")
def ws(ws):
    connected_clients.add(ws)
    try:
        events = build_initial_events()
        for event in events:
            ws.send(json.dumps(event))
        while True:
            raw = ws.receive()
            if raw is None:
                break
            try:
                msg = json.loads(raw)
                broadcast_message(msg, exclude_client=ws)
            except (json.JSONDecodeError, TypeError):
                pass
    finally:
        connected_clients.discard(ws)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

import json
import os

from flask import Flask, Response, jsonify, request
from flask_sock import Sock

from api.mock_data import RECORDS, STYLI

app = Flask(__name__, static_folder="../ui", static_url_path="")
sock = Sock(app)

# Connected WebSocket clients for event broadcasting
connected_clients: set = set()


@app.route("/")
def index():
    return app.send_static_file("index.html")


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@app.get("/records")
def list_records():
    return jsonify([r.model_dump() for r in RECORDS.values()])


@app.get("/records/<id>")
def get_record(id):
    record = RECORDS.get(id)
    if record is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(record.model_dump())


@app.post("/records/<id>/link")
def link_record(id):
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

            yield "data: " + json.dumps({"status": "Updating database"}) + "\n\n"
            styli, records = extract_data(TMP_REPO_DIR)
            upsert_styli(styli)
            upsert_records(records)
            copy_images(TMP_REPO_DIR, IMAGES_DEST)
            update_sync_date()

            yield "data: " + json.dumps({"status": "Sync complete"}) + "\n\n"
        except Exception as e:
            app.logger.error("Sync error: %s", e)
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
    msg = json.dumps(data)
    for client in list(connected_clients):
        try:
            client.send(msg)
        except Exception:
            connected_clients.discard(client)
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@sock.route("/ws")
def ws(ws):
    connected_clients.add(ws)
    try:
        events = [
            {"event": "stylus_hours", "data": {"hours": 89.6, "stylus_id": "1"}},
            {"event": "temperature_c", "data": {"temp_c": 59}},
            {"event": "current_record", "data": {"record_id": "1"}},
            {"event": "status", "data": {"status": "idle"}},
        ]
        for event in events:
            ws.send(json.dumps(event))
        while True:
            raw = ws.receive()
            if raw is None:
                break
            try:
                msg = json.loads(raw)
                payload = json.dumps(msg)
                for client in list(connected_clients):
                    if client is not ws:
                        try:
                            client.send(payload)
                        except Exception:
                            connected_clients.discard(client)
            except (json.JSONDecodeError, TypeError):
                pass
    finally:
        connected_clients.discard(ws)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

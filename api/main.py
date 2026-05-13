import json

from flask import Flask, jsonify
from flask_sock import Sock

from api.mock_data import RECORDS, STYLI

app = Flask(__name__, static_folder="../ui", static_url_path="")
sock = Sock(app)


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


@app.post("/records/sync")
def sync_records():
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


@app.post("/styli/sync")
def sync_styli():
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Server control
# ---------------------------------------------------------------------------

@app.post("/shutdown")
def shutdown():
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@sock.route("/ws")
def ws(ws):
    events = [
        {"event": "stylus_hours", "data": {"hours": 89.6, "stylus_id": "1"}},
        {"event": "temperature_c", "data": {"temp_c": 59}},
        {"event": "current_record", "data": {"record_id": "1"}},
        {"event": "status", "data": {"status": "idle"}},
    ]
    for event in events:
        ws.send(json.dumps(event))
    while True:
        ws.receive()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

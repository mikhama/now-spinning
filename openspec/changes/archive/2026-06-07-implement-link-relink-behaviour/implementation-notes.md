## Manual Frontend Checks

Run the app in boardless mode:

```bash
BOARDLESS_MODE=true python -m api.main
```

Open `http://127.0.0.1:5000/#link`.

1. Click `Link`; the selected record remains visible and a blinking dot appears under the linked status label.
2. In another terminal, send:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"event":"link_success","data":{"record_id":"1"}}' http://localhost:5000/events
```

3. The blinking dot disappears, the record state becomes linked, and pressing `Next` then `Prev` does not show that linked record in link mode.
4. Repeat link successes for remaining unlinked records until the view shows `No unlinked records` and only the Mode action is active.
5. Open `http://127.0.0.1:5000/#re-link`; only linked records are shown, `Next`/`Prev` wraps through linked records, and a successful re-link remains reachable.
6. Click `Re-Link`; the blinking dot appears under the linked label.
7. Send:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"event":"link_error","data":{"record_id":"1"}}' http://localhost:5000/events
```

8. The blinking dot clears and the Link Error state appears in the active link or re-link mode.

If there are no linked records, `http://127.0.0.1:5000/#re-link` shows `No linked records` and only the Mode action is active.

## Boardless Curl Examples

Successful link result:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"event":"link_success","data":{"record_id":"1"}}' http://localhost:5000/events
```

Failed link result:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"event":"link_error","data":{"record_id":"1"}}' http://localhost:5000/events
```

## Verification Run

On 2026-06-07, port 5000 was already occupied by another process, so the updated app from this checkout was started on port 5001:

```bash
BOARDLESS_MODE=true env/bin/python -c "from api.main import app; app.run(host='127.0.0.1', port=5001)"
```

The equivalent boardless event commands were verified against the updated app:

```bash
curl -s -i -X POST -H 'Content-Type: application/json' -d '{"event":"link_success","data":{"record_id":"1"}}' http://localhost:5001/events
curl -s -i -X POST -H 'Content-Type: application/json' -d '{"event":"link_error","data":{"record_id":"1"}}' http://localhost:5001/events
```

Both returned `HTTP/1.1 200 OK` with `{"success":true}`. The `link_success` command persisted record `1` as `linked = 1`; the verification side effect was restored to `linked = 0` afterward.

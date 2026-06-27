#!/bin/sh
set -eu

APP_URL="http://127.0.0.1:5000/"
MAX_READINESS_ATTEMPTS=60
APP_PID=""
CHROMIUM_PID=""
CHROMIUM_PROFILE_DIR=""

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
VENV_ACTIVATE="$REPO_ROOT/env/bin/activate"

cleanup() {
    status=$?
    trap - EXIT INT TERM HUP

    if [ -n "$APP_PID" ] && kill -0 "$APP_PID" 2>/dev/null; then
        kill "$APP_PID" 2>/dev/null || true
        wait "$APP_PID" 2>/dev/null || true
    fi

    if [ -n "$CHROMIUM_PID" ] && kill -0 "$CHROMIUM_PID" 2>/dev/null; then
        kill "$CHROMIUM_PID" 2>/dev/null || true
        wait "$CHROMIUM_PID" 2>/dev/null || true
    fi

    if [ -n "$CHROMIUM_PROFILE_DIR" ] && [ -d "$CHROMIUM_PROFILE_DIR" ]; then
        rm -rf "$CHROMIUM_PROFILE_DIR"
    fi

    exit "$status"
}

trap cleanup EXIT INT TERM HUP

if [ ! -f "$VENV_ACTIVATE" ]; then
    echo "Error: project virtualenv is required at env/. Create it and install dependencies before running kiosk mode." >&2
    echo "Expected activation script: $VENV_ACTIVATE" >&2
    exit 1
fi

if ! command -v chromium >/dev/null 2>&1; then
    echo "Error: Chromium is required for kiosk mode. Install chromium or make the chromium command available on PATH." >&2
    exit 1
fi

. "$VENV_ACTIVATE"

cd "$REPO_ROOT"
KIOSK_SHUTDOWN_ENABLED=true
export KIOSK_SHUTDOWN_ENABLED
python -m api.main &
APP_PID=$!

attempt=1
while [ "$attempt" -le "$MAX_READINESS_ATTEMPTS" ]; do
    if ! kill -0 "$APP_PID" 2>/dev/null; then
        wait "$APP_PID" 2>/dev/null || true
        echo "Error: app process exited before $APP_URL became ready." >&2
        exit 1
    fi

    if python - "$APP_URL" <<'PY'
import sys
from urllib.request import urlopen

try:
    with urlopen(sys.argv[1], timeout=1):
        pass
except Exception:
    sys.exit(1)
PY
    then
        break
    fi

    attempt=$((attempt + 1))
    sleep 1
done

if [ "$attempt" -gt "$MAX_READINESS_ATTEMPTS" ]; then
    echo "Error: app did not become ready at $APP_URL within $MAX_READINESS_ATTEMPTS seconds." >&2
    exit 1
fi

CHROMIUM_PROFILE_DIR=$(mktemp -d "${TMPDIR:-/tmp}/now-spinning-kiosk.XXXXXX")

chromium \
    --kiosk \
    --no-first-run \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --user-data-dir="$CHROMIUM_PROFILE_DIR" \
    "$APP_URL" &
CHROMIUM_PID=$!

wait "$CHROMIUM_PID"

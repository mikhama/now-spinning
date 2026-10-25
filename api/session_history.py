"""Playback-counter history, called only while the application's playback lock is held."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from api.stylus_hours import parse_elapsed_seconds


@dataclass
class Segment:
    record_id: str
    started_at: datetime
    seconds: int = 0

    def row(self):
        return self.record_id, self.started_at.astimezone(timezone.utc).isoformat(), self.seconds


class SessionHistoryTracker:
    def __init__(self, record_exists, save_sessions, *, now=None, flush_interval_seconds=600):
        self.record_exists = record_exists
        self.save_sessions = save_sessions
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.flush_interval_seconds = flush_interval_seconds
        self.record_id = None
        self.last_elapsed_seconds = None
        self.closed_segments = []
        self.segment = None

    @property
    def pending_seconds(self):
        return sum(s.seconds for s in self.closed_segments) + (self.segment.seconds if self.segment else 0)

    @property
    def checkpoint_due(self):
        return bool(self.closed_segments) or self.pending_seconds >= self.flush_interval_seconds

    def _close_segment(self):
        if self.segment is not None and self.segment.seconds > 0:
            self.closed_segments.append(self.segment)
        self.segment = None
        self.last_elapsed_seconds = None

    def process_message(self, message, record_id):
        if message.get("event") not in ("scan", "current_record", "status"):
            return

        try:
            resolved = str(record_id) if record_id is not None and str(record_id).strip() and self.record_exists(record_id) else None
        except Exception:
            # An unavailable lookup must not extend the previously identified record.
            self._close_segment()
            self.record_id = None
            raise
        if resolved != self.record_id:
            self._close_segment()
            self.record_id = resolved

        if message.get("event") != "status":
            return
        data = message.get("data") or {}
        if data.get("status") == "stop":
            self._close_segment()
            return
        if data.get("status") != "play":
            return
        elapsed = parse_elapsed_seconds(data.get("time"))
        if elapsed is None:
            return
        previous = self.last_elapsed_seconds
        if previous is not None and elapsed < previous:
            self._close_segment()
            previous = None
        self.last_elapsed_seconds = elapsed
        if resolved is None or previous is None or elapsed <= previous:
            return

        seconds = elapsed - previous
        if self.segment is None:
            self.segment = Segment(resolved, self.now().astimezone(timezone.utc) - timedelta(seconds=seconds))
        self.segment.seconds += seconds

    def flush_pending(self):
        segments = list(self.closed_segments)
        if self.segment is not None and self.segment.seconds > 0:
            segments.append(self.segment)
        if not segments:
            return True
        if self.save_sessions([s.row() for s in segments]) is not True:
            return False
        # The save callback has committed. No mutation happens before acknowledgement.
        self.closed_segments.clear()
        if self.segment is not None:
            self.segment.started_at += timedelta(seconds=self.segment.seconds)
            self.segment.seconds = 0
        return True

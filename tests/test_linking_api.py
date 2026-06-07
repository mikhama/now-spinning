import json
import os
import tempfile
import unittest
from unittest.mock import patch

from api.main import app
from api.services.db import database


class LinkingApiTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.original_db_path = database.DB_PATH
        database.DB_PATH = os.path.join(self.tmpdir.name, "now-spinning.db")
        database.init_db()
        self.client = app.test_client()

    def tearDown(self):
        database.DB_PATH = self.original_db_path
        self.tmpdir.cleanup()

    def insert_record(self, record_id="1", linked=0):
        conn = database._get_connection()
        try:
            conn.execute(
                "INSERT INTO record (id, release_id, master_id, title, artist, sides, linked) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (record_id, "release-" + record_id, "master-" + record_id, "Title", "Artist", json.dumps([]), linked),
            )
            conn.commit()
        finally:
            conn.close()

    def get_linked_value(self, record_id="1"):
        conn = database._get_connection()
        try:
            row = conn.execute("SELECT linked FROM record WHERE id = ?", (record_id,)).fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def test_mark_record_linked_reports_updated_rows(self):
        self.insert_record("1", linked=0)

        self.assertTrue(database.mark_record_linked("1"))
        self.assertEqual(self.get_linked_value("1"), 1)
        self.assertFalse(database.mark_record_linked("999"))

    def test_records_link_endpoint_persists_or_returns_404(self):
        self.insert_record("1", linked=0)

        response = self.client.post("/records/1/link")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"success": True})
        self.assertEqual(self.get_linked_value("1"), 1)

        missing_response = self.client.post("/records/999/link")
        self.assertEqual(missing_response.status_code, 404)

    def test_link_success_event_validates_persists_then_broadcasts(self):
        self.insert_record("1", linked=0)
        payload = {"event": "link_success", "data": {"record_id": "1"}}

        with patch("api.main.broadcast_message") as broadcast_message:
            response = self.client.post("/events", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"success": True})
        self.assertEqual(self.get_linked_value("1"), 1)
        broadcast_message.assert_called_once_with(payload)

    def test_link_success_event_rejects_missing_or_unknown_record_id(self):
        with patch("api.main.broadcast_message") as broadcast_message:
            missing_response = self.client.post("/events", json={"event": "link_success", "data": {}})
            unknown_response = self.client.post(
                "/events",
                json={"event": "link_success", "data": {"record_id": "999"}},
            )

        self.assertEqual(missing_response.status_code, 400)
        self.assertEqual(unknown_response.status_code, 404)
        broadcast_message.assert_not_called()

    def test_link_error_event_is_broadcast(self):
        payload = {"event": "link_error", "data": {"record_id": "1"}}

        with patch("api.main.broadcast_message") as broadcast_message:
            response = self.client.post("/events", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"success": True})
        broadcast_message.assert_called_once_with(payload)


if __name__ == "__main__":
    unittest.main()

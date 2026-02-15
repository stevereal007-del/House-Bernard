"""Integration tests for the House Bernard platform.

Tests the database, message bus, agent delegation, and web routes
end-to-end.  Uses a temporary database so nothing touches production.
"""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

# Point DB to a temp file before importing platform modules
_tmpdir = tempfile.mkdtemp()
os.environ["HB_TEST_DB"] = str(Path(_tmpdir) / "test.db")

# Patch config before anything imports it
import hb_platform.config as cfg
cfg.DB_PATH = Path(os.environ["HB_TEST_DB"])

from hb_platform.database import get_db, init_db
from hb_platform.agents import message_bus
from hb_platform.agents.achillesrun import delegate, on_artifact_submitted
from hb_platform.auth import generate_secret, generate_token, verify_token


class TestDatabase(unittest.TestCase):
    def setUp(self):
        cfg.DB_PATH = Path(_tmpdir) / f"test_{id(self)}.db"
        init_db()

    def tearDown(self):
        if cfg.DB_PATH.exists():
            cfg.DB_PATH.unlink()

    def test_schema_created(self):
        with get_db() as conn:
            tables = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()]
        self.assertIn("citizens", tables)
        self.assertIn("forum_topics", tables)
        self.assertIn("forum_threads", tables)
        self.assertIn("forum_posts", tables)
        self.assertIn("briefs", tables)
        self.assertIn("submissions", tables)
        self.assertIn("agent_messages", tables)

    def test_default_forum_topics_seeded(self):
        with get_db() as conn:
            topics = conn.execute("SELECT name FROM forum_topics ORDER BY id").fetchall()
        names = [t["name"] for t in topics]
        self.assertIn("General", names)
        self.assertIn("Announcements", names)
        self.assertIn("Research", names)

    def test_citizen_crud(self):
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            conn.execute(
                "INSERT INTO citizens (id, alias, joined_at) VALUES (?, ?, ?)",
                ("HB-CIT-0001", "TestUser", now),
            )
            row = conn.execute(
                "SELECT * FROM citizens WHERE id = ?", ("HB-CIT-0001",)
            ).fetchone()
        self.assertEqual(row["alias"], "TestUser")
        self.assertEqual(row["tier"], "visitor")
        self.assertEqual(row["total_earned"], 0.0)


class TestMessageBus(unittest.TestCase):
    def setUp(self):
        cfg.DB_PATH = Path(_tmpdir) / f"test_bus_{id(self)}.db"
        init_db()

    def tearDown(self):
        if cfg.DB_PATH.exists():
            cfg.DB_PATH.unlink()

    def test_send_and_poll(self):
        msg_id = message_bus.send("achillesrun", "warden", "task",
                                  {"action": "evaluate_artifact"})
        self.assertIsInstance(msg_id, int)

        pending = message_bus.poll("warden")
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["from_agent"], "achillesrun")

    def test_ack_removes_from_poll(self):
        msg_id = message_bus.send("achillesrun", "warden", "task", {"action": "test"})
        message_bus.ack(msg_id)
        pending = message_bus.poll("warden")
        self.assertEqual(len(pending), 0)

    def test_respond(self):
        msg_id = message_bus.send("achillesrun", "warden", "task", {"action": "test"})
        resp_id = message_bus.respond(msg_id, "warden", {"result": "ok"})
        pending = message_bus.poll("achillesrun")
        self.assertTrue(any(p["id"] == resp_id for p in pending))

    def test_heartbeat(self):
        msg_id = message_bus.heartbeat("warden")
        self.assertIsInstance(msg_id, int)
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM agent_messages WHERE id = ?", (msg_id,)
            ).fetchone()
        self.assertEqual(row["message_type"], "heartbeat")
        self.assertEqual(row["from_agent"], "warden")

    def test_priority_ordering(self):
        message_bus.send("a", "warden", "task", {"p": "low"}, priority="low")
        message_bus.send("a", "warden", "task", {"p": "emergency"}, priority="emergency")
        message_bus.send("a", "warden", "task", {"p": "normal"}, priority="normal")
        msgs = message_bus.poll("warden", limit=10)
        priorities = [json.loads(m["payload"])["p"] for m in msgs]
        self.assertEqual(priorities, ["emergency", "normal", "low"])

    def test_recent(self):
        message_bus.send("a", "b", "task", {"x": 1})
        message_bus.send("c", "d", "task", {"x": 2})
        recent = message_bus.recent(limit=5)
        self.assertEqual(len(recent), 2)


class TestDelegation(unittest.TestCase):
    def setUp(self):
        cfg.DB_PATH = Path(_tmpdir) / f"test_deleg_{id(self)}.db"
        init_db()

    def tearDown(self):
        if cfg.DB_PATH.exists():
            cfg.DB_PATH.unlink()

    def test_delegate_routes_to_correct_agent(self):
        msg_id = delegate("evaluate_artifact", {"hash": "abc"})
        self.assertIsNotNone(msg_id)
        msgs = message_bus.poll("warden")
        self.assertEqual(len(msgs), 1)
        payload = json.loads(msgs[0]["payload"])
        self.assertEqual(payload["action"], "evaluate_artifact")

    def test_delegate_unknown_action_returns_none(self):
        result = delegate("nonexistent_action", {})
        self.assertIsNone(result)

    def test_on_artifact_submitted(self):
        msg_id = on_artifact_submitted("sha256:abc", "HB-CIT-0001", "HB-BRIEF-0001")
        self.assertIsInstance(msg_id, int)
        msgs = message_bus.poll("warden")
        self.assertEqual(len(msgs), 1)

    def test_cross_agent_messaging(self):
        """Magistrate bans a citizen → message goes to Warden."""
        # Simulate magistrate sending to warden
        message_bus.send("magistrate", "warden", "task",
                         {"action": "revoke_access", "citizen_id": "HB-CIT-0099"})
        msgs = message_bus.poll("warden")
        self.assertEqual(len(msgs), 1)
        payload = json.loads(msgs[0]["payload"])
        self.assertEqual(payload["action"], "revoke_access")
        self.assertEqual(payload["citizen_id"], "HB-CIT-0099")


class TestAuth(unittest.TestCase):
    def test_generate_and_verify_token(self):
        secret = generate_secret()
        token = generate_token("HB-CIT-0001", secret)
        result = verify_token(token, lambda cid: secret if cid == "HB-CIT-0001" else None)
        self.assertEqual(result, "HB-CIT-0001")

    def test_invalid_token_rejected(self):
        result = verify_token("bogus:token:value", lambda cid: None)
        self.assertIsNone(result)

    def test_wrong_secret_rejected(self):
        secret = generate_secret()
        token = generate_token("HB-CIT-0001", secret)
        result = verify_token(token, lambda cid: "wrong-secret")
        self.assertIsNone(result)

    def test_expired_token_rejected(self):
        import hb_platform.config as c
        old = c.TOKEN_EXPIRY_HOURS
        c.TOKEN_EXPIRY_HOURS = -1  # Already expired
        secret = generate_secret()
        token = generate_token("HB-CIT-0001", secret)
        result = verify_token(token, lambda cid: secret)
        c.TOKEN_EXPIRY_HOURS = old
        self.assertIsNone(result)


class TestForum(unittest.TestCase):
    def setUp(self):
        cfg.DB_PATH = Path(_tmpdir) / f"test_forum_{id(self)}.db"
        init_db()
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            conn.execute(
                "INSERT INTO citizens (id, alias, joined_at) VALUES (?, ?, ?)",
                ("HB-CIT-0001", "TestUser", now),
            )

    def tearDown(self):
        if cfg.DB_PATH.exists():
            cfg.DB_PATH.unlink()

    def test_create_thread_and_post(self):
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO forum_threads (topic_id, title, author_id, created_at) "
                "VALUES (1, 'Test Thread', 'HB-CIT-0001', ?)", (now,)
            )
            thread_id = cur.lastrowid
            conn.execute(
                "INSERT INTO forum_posts (thread_id, author_id, body, created_at) "
                "VALUES (?, 'HB-CIT-0001', 'Hello world', ?)", (thread_id, now)
            )
            posts = conn.execute(
                "SELECT * FROM forum_posts WHERE thread_id = ?", (thread_id,)
            ).fetchall()
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]["body"], "Hello world")

    def test_thread_count_per_topic(self):
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            conn.execute(
                "INSERT INTO forum_threads (topic_id, title, author_id, created_at) "
                "VALUES (1, 'Thread A', 'HB-CIT-0001', ?)", (now,)
            )
            conn.execute(
                "INSERT INTO forum_threads (topic_id, title, author_id, created_at) "
                "VALUES (1, 'Thread B', 'HB-CIT-0001', ?)", (now,)
            )
            count = conn.execute(
                "SELECT COUNT(*) FROM forum_threads WHERE topic_id = 1"
            ).fetchone()[0]
        self.assertEqual(count, 2)


class TestSubmissions(unittest.TestCase):
    def setUp(self):
        cfg.DB_PATH = Path(_tmpdir) / f"test_sub_{id(self)}.db"
        init_db()
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            conn.execute(
                "INSERT INTO citizens (id, alias, joined_at) VALUES (?, ?, ?)",
                ("HB-CIT-0001", "TestUser", now),
            )

    def tearDown(self):
        if cfg.DB_PATH.exists():
            cfg.DB_PATH.unlink()

    def test_submit_and_query(self):
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            conn.execute(
                "INSERT INTO submissions (citizen_id, artifact_hash, status, submitted_at) "
                "VALUES ('HB-CIT-0001', 'sha256:abc', 'queued', ?)", (now,)
            )
            rows = conn.execute(
                "SELECT * FROM submissions WHERE citizen_id = 'HB-CIT-0001'"
            ).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "queued")

    def test_status_counts(self):
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            conn.execute(
                "INSERT INTO submissions (citizen_id, artifact_hash, status, submitted_at) "
                "VALUES ('HB-CIT-0001', 'sha256:a', 'survived', ?)", (now,)
            )
            conn.execute(
                "INSERT INTO submissions (citizen_id, artifact_hash, status, submitted_at) "
                "VALUES ('HB-CIT-0001', 'sha256:b', 'culled', ?)", (now,)
            )
            conn.execute(
                "INSERT INTO submissions (citizen_id, artifact_hash, status, submitted_at) "
                "VALUES ('HB-CIT-0001', 'sha256:c', 'queued', ?)", (now,)
            )
            row = conn.execute(
                "SELECT "
                "  SUM(status='survived') AS survived, "
                "  SUM(status='culled') AS culled, "
                "  SUM(status='queued') AS queued "
                "FROM submissions"
            ).fetchone()
        self.assertEqual(row["survived"], 1)
        self.assertEqual(row["culled"], 1)
        self.assertEqual(row["queued"], 1)


if __name__ == "__main__":
    unittest.main()

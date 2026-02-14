#!/usr/bin/env python3
"""
Tests for S9-W-006: Dead Man's Switch
Classification: CROWN EYES ONLY
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add weapons dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from S9_W_006_heartbeat import send_heartbeat  # noqa: E402
from S9_W_006_monitor import (  # noqa: E402
    read_heartbeat,
    count_missed_heartbeats,
    check_status,
    HEARTBEAT_INTERVAL_HOURS,
    GRACE_HOURS,
    WARNING_THRESHOLD,
    CRITICAL_THRESHOLD,
    ACTIVATION_THRESHOLD,
)
from S9_W_006_lockdown import execute_lockdown  # noqa: E402


# === Heartbeat Tests ===

class TestHeartbeat:
    def test_writes_correct_fields(self, tmp_path: Path) -> None:
        """Heartbeat should contain all required fields."""
        hb_path = tmp_path / "heartbeat.json"
        threats_path = tmp_path / "THREATS.md"
        threats_path.write_text("# Test threats")

        result = send_heartbeat(hb_path, threats_path, tmp_path / "backup.json")

        assert result["status"] == "alive"
        assert result["sequence"] == 1
        assert "timestamp" in result
        assert "threats_hash" in result

    def test_increments_sequence(self, tmp_path: Path) -> None:
        """Each heartbeat should increment the sequence number."""
        hb_path = tmp_path / "heartbeat.json"
        threats_path = tmp_path / "THREATS.md"
        threats_path.write_text("# Threats")

        r1 = send_heartbeat(hb_path, threats_path, tmp_path / "backup.json")
        r2 = send_heartbeat(hb_path, threats_path, tmp_path / "backup.json")
        r3 = send_heartbeat(hb_path, threats_path, tmp_path / "backup.json")

        assert r1["sequence"] == 1
        assert r2["sequence"] == 2
        assert r3["sequence"] == 3

    def test_writes_primary_and_backup(self, tmp_path: Path) -> None:
        """Both primary and backup files should be written."""
        hb_path = tmp_path / "primary" / "heartbeat.json"
        backup_path = tmp_path / "backup" / "heartbeat.json"
        threats_path = tmp_path / "THREATS.md"
        threats_path.write_text("test")

        send_heartbeat(hb_path, threats_path, backup_path)

        assert hb_path.exists()
        assert backup_path.exists()


# === Monitor Tests ===

class TestMonitor:
    def test_fresh_heartbeat_ok(self, tmp_path: Path) -> None:
        """A fresh heartbeat should report OK."""
        hb_path = tmp_path / "heartbeat.json"
        now = datetime.now(timezone.utc)
        hb_path.write_text(json.dumps({
            "timestamp": now.isoformat(),
            "status": "alive",
            "sequence": 1,
            "threats_hash": "abc",
        }))

        status = check_status(hb_path, now)
        assert status["level"] == "OK"
        assert status["missed_heartbeats"] == 0

    def test_3_missed_warning(self, tmp_path: Path) -> None:
        """3 missed heartbeats = WARNING."""
        hb_path = tmp_path / "heartbeat.json"
        now = datetime.now(timezone.utc)
        old = now - timedelta(hours=HEARTBEAT_INTERVAL_HOURS * 3 + GRACE_HOURS + 1)
        hb_path.write_text(json.dumps({
            "timestamp": old.isoformat(),
            "status": "alive",
            "sequence": 5,
            "threats_hash": "abc",
        }))

        status = check_status(hb_path, now)
        assert status["missed_heartbeats"] >= WARNING_THRESHOLD
        assert status["level"] in ("WARNING", "CRITICAL", "ACTIVATION")

    def test_6_missed_activation(self, tmp_path: Path) -> None:
        """6 missed heartbeats = ACTIVATION."""
        hb_path = tmp_path / "heartbeat.json"
        now = datetime.now(timezone.utc)
        old = now - timedelta(hours=HEARTBEAT_INTERVAL_HOURS * 7)
        hb_path.write_text(json.dumps({
            "timestamp": old.isoformat(),
            "status": "alive",
            "sequence": 10,
            "threats_hash": "abc",
        }))

        status = check_status(hb_path, now)
        assert status["missed_heartbeats"] >= ACTIVATION_THRESHOLD
        assert status["level"] == "ACTIVATION"

    def test_missing_file_no_activation(self, tmp_path: Path) -> None:
        """Missing heartbeat file = 'never started', NOT missed."""
        hb_path = tmp_path / "nonexistent.json"
        status = check_status(hb_path)
        assert status["level"] == "NO_HEARTBEAT"
        assert status["missed_heartbeats"] == 0

    def test_malformed_json_no_activation(self, tmp_path: Path) -> None:
        """Malformed heartbeat.json should not trigger activation."""
        hb_path = tmp_path / "heartbeat.json"
        hb_path.write_text("not valid json{{{")
        status = check_status(hb_path)
        assert status["level"] == "NO_HEARTBEAT"
        assert status["missed_heartbeats"] == 0

    def test_missing_timestamp_no_activation(self, tmp_path: Path) -> None:
        """Heartbeat with missing timestamp should not trigger."""
        hb_path = tmp_path / "heartbeat.json"
        hb_path.write_text(json.dumps({"status": "alive", "sequence": 1}))
        status = check_status(hb_path)
        assert status["missed_heartbeats"] == 0


# === Lockdown Tests ===

class TestLockdown:
    def test_simulation_mode_no_writes(self, tmp_path: Path) -> None:
        """Simulation mode should not write any files."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "test.txt").write_text("hello")

        hb_path = tmp_path / "heartbeat.json"
        log_path = tmp_path / "LOG.md"
        log_path.write_text("# Log\n")

        result = execute_lockdown(
            repo_path=repo,
            heartbeat_path=hb_path,
            log_path=log_path,
            live=False,
        )

        assert result["mode"] == "simulation"
        assert result["live"] is False
        assert not hb_path.exists()  # Should NOT have been written
        # Log should be unchanged
        assert log_path.read_text() == "# Log\n"

    def test_live_flag_required(self, tmp_path: Path) -> None:
        """Without --live, lockdown should be simulation only."""
        result = execute_lockdown(
            repo_path=tmp_path,
            heartbeat_path=tmp_path / "hb.json",
            log_path=tmp_path / "log.md",
            live=False,
        )
        assert result["live"] is False
        assert result["mode"] == "simulation"

    def test_snapshot_hash_computed(self, tmp_path: Path) -> None:
        """Snapshot should produce a valid SHA256 hash."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "file1.txt").write_text("content1")
        (repo / "file2.txt").write_text("content2")

        result = execute_lockdown(
            repo_path=repo,
            heartbeat_path=tmp_path / "hb.json",
            log_path=tmp_path / "log.md",
            live=False,
        )

        assert len(result["snapshot_hash"]) == 64  # SHA256 hex

    def test_live_writes_files(self, tmp_path: Path) -> None:
        """Live mode should write heartbeat and log."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "test.txt").write_text("data")

        hb_path = tmp_path / "heartbeat.json"
        log_path = tmp_path / "LOG.md"
        log_path.write_text("# Log\n")

        result = execute_lockdown(
            repo_path=repo,
            heartbeat_path=hb_path,
            log_path=log_path,
            live=True,
        )

        assert result["live"] is True
        assert hb_path.exists()
        hb_data = json.loads(hb_path.read_text())
        assert hb_data["status"] == "LOCKDOWN"
        assert "DEAD MAN'S SWITCH ACTIVATION" in log_path.read_text()

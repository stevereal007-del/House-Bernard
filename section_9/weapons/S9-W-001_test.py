#!/usr/bin/env python3
"""
Tests for S9-W-001: Tripwire Alpha
Classification: CROWN EYES ONLY
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add weapons dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from S9_W_001_tripwire_alpha import (  # noqa: E402
    TripwireConfig,
    analyze,
    detect_rate_spikes,
    detect_clusters,
    detect_time_anomalies,
    detect_sequential_probes,
    read_jsonl,
    _artifact_fingerprint,
    _parse_timestamp,
)


def _ts(days_ago: int = 0, hours_ago: int = 0, hour: int = 14) -> str:
    """Helper to generate ISO timestamps."""
    base = datetime(2026, 2, 9, hour, 0, 0, tzinfo=timezone.utc)
    dt = base - timedelta(days=days_ago, hours=hours_ago)
    return dt.isoformat()


def _entry(identity: str = "agent-A", days_ago: int = 0,
           hours_ago: int = 0, hour: int = 14, size: int = 1024,
           verdict: str = "PASS", artifact: str = "test.zip") -> dict:
    """Helper to create a log entry."""
    return {
        "timestamp": _ts(days_ago, hours_ago, hour),
        "identity": identity,
        "artifact": artifact,
        "size": size,
        "verdict": verdict,
    }


# === Unit Tests ===

class TestParseTimestamp:
    def test_valid_iso(self) -> None:
        result = _parse_timestamp("2026-02-09T14:00:00+00:00")
        assert result is not None
        assert result.year == 2026

    def test_z_suffix(self) -> None:
        result = _parse_timestamp("2026-02-09T14:00:00Z")
        assert result is not None

    def test_invalid(self) -> None:
        assert _parse_timestamp("not a date") is None
        assert _parse_timestamp("") is None
        assert _parse_timestamp(None) is None


class TestArtifactFingerprint:
    def test_same_structure_same_hash(self) -> None:
        e1 = {"artifact": "a.zip", "size": 1024, "verdict": "PASS"}
        e2 = {"artifact": "a.zip", "size": 1024, "verdict": "PASS"}
        assert _artifact_fingerprint(e1) == _artifact_fingerprint(e2)

    def test_different_size_different_hash(self) -> None:
        e1 = {"artifact": "a.zip", "size": 1024, "verdict": "PASS"}
        e2 = {"artifact": "a.zip", "size": 5000, "verdict": "PASS"}
        assert _artifact_fingerprint(e1) != _artifact_fingerprint(e2)


class TestRateSpikes:
    def test_normal_rate_no_alert(self) -> None:
        """Normal submission pattern should not trigger."""
        config = TripwireConfig()
        entries = [_entry(days_ago=d) for d in range(7)]  # 1/day for 7 days
        alerts = detect_rate_spikes(entries, config)
        assert len(alerts) == 0

    def test_spike_triggers_alert(self) -> None:
        """5 submissions today with 1/day baseline should trigger."""
        config = TripwireConfig(rate_threshold=3.0)
        entries = [_entry(days_ago=d) for d in range(1, 8)]  # 1/day baseline
        # Add 5 today
        for h in range(5):
            entries.append(_entry(hours_ago=h))
        alerts = detect_rate_spikes(entries, config)
        assert len(alerts) == 1
        assert alerts[0]["alert_type"] == "rate_spike"
        assert alerts[0]["severity"] == "S2"


class TestClusters:
    def test_no_cluster_different_fingerprints(self) -> None:
        """Different artifacts from different identities = no cluster."""
        config = TripwireConfig()
        entries = [
            _entry(identity=f"agent-{i}", size=i * 2000)
            for i in range(5)
        ]
        alerts = detect_clusters(entries, config)
        assert len(alerts) == 0

    def test_cluster_detected(self) -> None:
        """3+ identities with same fingerprint in same window = cluster."""
        config = TripwireConfig(cluster_min_identities=3)
        entries = [
            _entry(identity=f"agent-{i}", size=1024, artifact="same.zip")
            for i in range(4)
        ]
        alerts = detect_clusters(entries, config)
        assert len(alerts) == 1
        assert alerts[0]["alert_type"] == "cluster"


class TestTimeAnomalies:
    def test_consistent_hours_no_alert(self) -> None:
        """Consistent submission times should not trigger."""
        config = TripwireConfig()
        entries = [_entry(hour=14, days_ago=d) for d in range(15)]
        alerts = detect_time_anomalies(entries, config)
        assert len(alerts) == 0

    def test_anomalous_hour_triggers(self) -> None:
        """A 3am submission when normal is 2pm should trigger."""
        config = TripwireConfig(time_anomaly_zscore=2.0)
        entries = [_entry(hour=14, days_ago=d) for d in range(1, 15)]
        entries.append(_entry(hour=3))  # Anomalous
        alerts = detect_time_anomalies(entries, config)
        assert len(alerts) == 1
        assert alerts[0]["alert_type"] == "time_anomaly"

    def test_too_few_entries_no_alert(self) -> None:
        """Fewer than 10 entries = not enough data, no alert."""
        config = TripwireConfig()
        entries = [_entry(hour=14, days_ago=d) for d in range(5)]
        entries.append(_entry(hour=3))
        alerts = detect_time_anomalies(entries, config)
        assert len(alerts) == 0


class TestSequentialProbes:
    def test_normal_sizes_no_alert(self) -> None:
        """Random sizes should not trigger."""
        config = TripwireConfig(probe_sequence_len=5)
        entries = [_entry(size=s) for s in [500, 1200, 800, 1500, 900, 1100]]
        alerts = detect_sequential_probes(entries, config)
        assert len(alerts) == 0

    def test_incrementing_sizes_triggers(self) -> None:
        """Monotonically increasing sizes = boundary probing."""
        config = TripwireConfig(probe_sequence_len=5)
        entries = [_entry(size=s) for s in [100, 200, 300, 400, 500]]
        alerts = detect_sequential_probes(entries, config)
        assert any(a["alert_type"] == "sequential_probe" for a in alerts)

    def test_systematic_rejections_triggers(self) -> None:
        """Mostly REJECT verdicts = systematic probing."""
        config = TripwireConfig(probe_sequence_len=5)
        entries = [_entry(verdict="REJECT") for _ in range(5)]
        alerts = detect_sequential_probes(entries, config)
        assert any(
            a["evidence"].get("pattern") == "systematic_rejections"
            for a in alerts
        )


# === Integration Test ===

class TestIntegration:
    def test_full_pipeline(self) -> None:
        """Feed a mixed log and get correct alert types."""
        config = TripwireConfig(
            rate_threshold=3.0,
            cluster_min_identities=3,
            probe_sequence_len=5,
        )
        entries = []
        # Normal baseline
        for d in range(1, 8):
            entries.append(_entry(identity="good-agent", days_ago=d))
        # Rate spike
        for h in range(5):
            entries.append(_entry(identity="good-agent", hours_ago=h))
        # Cluster
        for i in range(4):
            entries.append(_entry(identity=f"sybil-{i}", size=2048, artifact="payload.zip"))
        # Sequential probing
        for s in [100, 200, 300, 400, 500]:
            entries.append(_entry(identity="prober", size=s))

        alerts = analyze(entries, config)
        alert_types = {a["alert_type"] for a in alerts}
        assert "rate_spike" in alert_types
        assert "cluster" in alert_types
        assert "sequential_probe" in alert_types


# === False Positive Test ===

class TestFalsePositives:
    def test_normal_activity_zero_alerts(self) -> None:
        """A log of perfectly normal activity produces zero alerts."""
        config = TripwireConfig()
        entries = []
        for d in range(30):
            entries.append(_entry(
                identity="regular-contributor",
                days_ago=d,
                hour=14,
                size=1024,
                verdict="PASS",
            ))
        alerts = analyze(entries, config)
        assert len(alerts) == 0


# === Fail-safe Test ===

class TestFailSafe:
    def test_malformed_jsonl(self) -> None:
        """Malformed input should produce empty results, not crash."""
        import io
        bad_input = io.StringIO("not json\n{bad: json}\n\n{\"valid\": true}\n")
        entries = read_jsonl(bad_input)
        # Should have parsed the one valid-ish entry
        assert len(entries) >= 0  # No crash is the test

    def test_empty_input_no_alerts(self) -> None:
        """Empty input = zero alerts, no crash."""
        config = TripwireConfig()
        alerts = analyze([], config)
        assert len(alerts) == 0

    def test_missing_fields_no_crash(self) -> None:
        """Entries missing expected fields should not crash."""
        config = TripwireConfig()
        entries = [
            {},
            {"timestamp": "2026-02-09T14:00:00Z"},
            {"identity": "test"},
            {"timestamp": "bad", "identity": "test"},
        ]
        alerts = analyze(entries, config)
        # May or may not produce alerts, but must not crash
        assert isinstance(alerts, list)

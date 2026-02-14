#!/usr/bin/env python3
"""
S9-W-001: Tripwire Alpha — Airlock Anomaly Detection
Classification: CROWN EYES ONLY
Class I (Passive) — Director authorization

Monitors Airlock submission logs for anomalous patterns.
Produces alert JSON. Never blocks, never modifies.
Fails to passive: if it crashes, no alerts fire.

Usage:
    python3 S9-W-001_tripwire_alpha.py <logfile.jsonl>
    python3 S9-W-001_tripwire_alpha.py --dry-run <logfile.jsonl>
    python3 S9-W-001_tripwire_alpha.py --threshold 2.0 <logfile.jsonl>
    cat logfile.jsonl | python3 S9-W-001_tripwire_alpha.py -
"""

from __future__ import annotations

import json
import sys
import math
import hashlib
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Optional


# === Configuration ===

DEFAULT_RATE_THRESHOLD: float = 3.0   # multiplier over 7-day rolling avg
DEFAULT_CLUSTER_WINDOW_HOURS: int = 4  # window for cluster detection
DEFAULT_CLUSTER_MIN_IDENTITIES: int = 3  # min distinct IDs for cluster
DEFAULT_TIME_ANOMALY_ZSCORE: float = 2.5  # z-score for hour-of-day anomaly
DEFAULT_PROBE_SEQUENCE_LEN: int = 5    # min sequential submissions for probe detection


class TripwireConfig:
    """Runtime configuration for Tripwire Alpha."""
    def __init__(
        self,
        rate_threshold: float = DEFAULT_RATE_THRESHOLD,
        cluster_window_hours: int = DEFAULT_CLUSTER_WINDOW_HOURS,
        cluster_min_identities: int = DEFAULT_CLUSTER_MIN_IDENTITIES,
        time_anomaly_zscore: float = DEFAULT_TIME_ANOMALY_ZSCORE,
        probe_sequence_len: int = DEFAULT_PROBE_SEQUENCE_LEN,
        dry_run: bool = False,
    ) -> None:
        self.rate_threshold = rate_threshold
        self.cluster_window_hours = cluster_window_hours
        self.cluster_min_identities = cluster_min_identities
        self.time_anomaly_zscore = time_anomaly_zscore
        self.probe_sequence_len = probe_sequence_len
        self.dry_run = dry_run


def _parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse ISO 8601 timestamp string to datetime. Returns None on failure."""
    try:
        if not isinstance(ts_str, str):
            return None
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None


def _make_alert(
    alert_type: str,
    severity: str,
    identity: str,
    evidence: dict,
    recommended_action: str,
) -> dict:
    """Create a standardized alert dict."""
    return {
        "weapon": "S9-W-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alert_type": alert_type,
        "severity": severity,
        "identity": identity,
        "evidence": evidence,
        "recommended_action": recommended_action,
    }


def _artifact_fingerprint(entry: dict) -> str:
    """Generate a structural fingerprint for an artifact entry."""
    parts = []
    if "artifact" in entry:
        parts.append(str(entry["artifact"]))
    if "size" in entry:
        # Bucket size to nearest 1KB for structural similarity
        bucket = (int(entry.get("size", 0)) // 1024) * 1024
        parts.append(f"size:{bucket}")
    if "verdict" in entry:
        parts.append(f"v:{entry['verdict']}")
    raw = "|".join(parts)
    return hashlib.md5(raw.encode()).hexdigest()[:12]


# === Detection Functions ===

def detect_rate_spikes(
    entries: list[dict],
    config: TripwireConfig,
) -> list[dict]:
    """Detect submission rate spikes per identity.

    A spike is when the recent rate (last 24h) exceeds
    the 7-day rolling average by the configured threshold.
    """
    alerts: list[dict] = []
    by_identity: dict[str, list[datetime]] = defaultdict(list)

    for entry in entries:
        ts = _parse_timestamp(entry.get("timestamp", ""))
        identity = entry.get("identity", "UNKNOWN")
        if ts is not None:
            by_identity[identity].append(ts)

    for identity, timestamps in by_identity.items():
        if len(timestamps) < 2:
            continue
        timestamps.sort()
        latest = timestamps[-1]
        window_7d = latest - timedelta(days=7)
        window_24h = latest - timedelta(hours=24)

        count_7d = sum(1 for t in timestamps if t >= window_7d)
        count_24h = sum(1 for t in timestamps if t >= window_24h)

        if count_7d == 0:
            continue

        avg_daily_7d = count_7d / 7.0
        if avg_daily_7d > 0 and count_24h > avg_daily_7d * config.rate_threshold:
            alerts.append(_make_alert(
                alert_type="rate_spike",
                severity="S2",
                identity=identity,
                evidence={
                    "count_24h": count_24h,
                    "avg_daily_7d": round(avg_daily_7d, 2),
                    "ratio": round(count_24h / avg_daily_7d, 2),
                    "threshold": config.rate_threshold,
                },
                recommended_action="investigate",
            ))
    return alerts


def detect_clusters(
    entries: list[dict],
    config: TripwireConfig,
) -> list[dict]:
    """Detect multiple identities submitting structurally similar artifacts."""
    alerts: list[dict] = []
    # Group entries by time window
    windowed: dict[str, list[dict]] = defaultdict(list)

    for entry in entries:
        ts = _parse_timestamp(entry.get("timestamp", ""))
        if ts is None:
            continue
        # Bucket by N-hour window
        bucket_key = ts.strftime("%Y-%m-%d") + f"_{ts.hour // config.cluster_window_hours}"
        windowed[bucket_key].append(entry)

    for bucket_key, bucket_entries in windowed.items():
        # Group by structural fingerprint within the window
        by_fingerprint: dict[str, set[str]] = defaultdict(set)
        for entry in bucket_entries:
            fp = _artifact_fingerprint(entry)
            identity = entry.get("identity", "UNKNOWN")
            by_fingerprint[fp].add(identity)

        for fp, identities in by_fingerprint.items():
            if len(identities) >= config.cluster_min_identities:
                alerts.append(_make_alert(
                    alert_type="cluster",
                    severity="S2",
                    identity="MULTIPLE",
                    evidence={
                        "fingerprint": fp,
                        "identities": sorted(identities),
                        "count": len(identities),
                        "window": bucket_key,
                    },
                    recommended_action="investigate",
                ))
    return alerts


def detect_time_anomalies(
    entries: list[dict],
    config: TripwireConfig,
) -> list[dict]:
    """Detect submissions at unusual hours for a given identity."""
    alerts: list[dict] = []
    by_identity: dict[str, list[int]] = defaultdict(list)

    for entry in entries:
        ts = _parse_timestamp(entry.get("timestamp", ""))
        identity = entry.get("identity", "UNKNOWN")
        if ts is not None:
            by_identity[identity].append(ts.hour)

    for identity, hours in by_identity.items():
        if len(hours) < 10:
            # Need enough data for statistical analysis
            continue

        # Compute mean and std of submission hours
        mean_hour = sum(hours) / len(hours)
        variance = sum((h - mean_hour) ** 2 for h in hours) / len(hours)
        std_hour = math.sqrt(variance) if variance > 0 else 0.0

        if std_hour < 0.5:
            # Very consistent — any deviation is suspicious but
            # std too small for meaningful z-score
            continue

        # Check the most recent submission
        latest_hour = hours[-1]
        zscore = abs(latest_hour - mean_hour) / std_hour

        if zscore > config.time_anomaly_zscore:
            alerts.append(_make_alert(
                alert_type="time_anomaly",
                severity="S1",
                identity=identity,
                evidence={
                    "latest_hour": latest_hour,
                    "mean_hour": round(mean_hour, 1),
                    "std_hour": round(std_hour, 1),
                    "zscore": round(zscore, 2),
                    "threshold": config.time_anomaly_zscore,
                },
                recommended_action="monitor",
            ))
    return alerts


def detect_sequential_probes(
    entries: list[dict],
    config: TripwireConfig,
) -> list[dict]:
    """Detect systematic boundary-testing patterns."""
    alerts: list[dict] = []
    by_identity: dict[str, list[dict]] = defaultdict(list)

    for entry in entries:
        identity = entry.get("identity", "UNKNOWN")
        by_identity[identity].append(entry)

    for identity, id_entries in by_identity.items():
        if len(id_entries) < config.probe_sequence_len:
            continue

        # Check for incrementing sizes (boundary probing)
        sizes = [e.get("size", 0) for e in id_entries if "size" in e]
        if len(sizes) >= config.probe_sequence_len:
            # Check if last N sizes are monotonically increasing
            tail = sizes[-config.probe_sequence_len:]
            if all(tail[i] < tail[i + 1] for i in range(len(tail) - 1)):
                alerts.append(_make_alert(
                    alert_type="sequential_probe",
                    severity="S2",
                    identity=identity,
                    evidence={
                        "pattern": "incrementing_sizes",
                        "sizes": tail,
                        "sequence_length": len(tail),
                    },
                    recommended_action="investigate",
                ))

        # Check for systematic rejection patterns (rotating banned imports)
        verdicts = [e.get("verdict", "") for e in id_entries]
        recent_verdicts = verdicts[-config.probe_sequence_len:]
        reject_count = sum(1 for v in recent_verdicts if v == "REJECT")
        if reject_count >= config.probe_sequence_len - 1:
            alerts.append(_make_alert(
                alert_type="sequential_probe",
                severity="S3",
                identity=identity,
                evidence={
                    "pattern": "systematic_rejections",
                    "recent_verdicts": recent_verdicts,
                    "reject_ratio": round(reject_count / len(recent_verdicts), 2),
                },
                recommended_action="escalate",
            ))
    return alerts


# === Main Pipeline ===

def analyze(entries: list[dict], config: TripwireConfig) -> list[dict]:
    """Run all detectors and return combined alerts."""
    alerts: list[dict] = []
    alerts.extend(detect_rate_spikes(entries, config))
    alerts.extend(detect_clusters(entries, config))
    alerts.extend(detect_time_anomalies(entries, config))
    alerts.extend(detect_sequential_probes(entries, config))
    return alerts


def read_jsonl(source) -> list[dict]:
    """Read JSONL entries from a file object. Silently skips malformed lines."""
    entries: list[dict] = []
    for line in source:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except (json.JSONDecodeError, TypeError):
            # Fail to passive: skip malformed lines
            continue
    return entries


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]
    config = TripwireConfig()

    # Parse flags
    while args and args[0].startswith("--"):
        flag = args.pop(0)
        if flag == "--dry-run":
            config.dry_run = True
        elif flag == "--threshold" and args:
            try:
                config.rate_threshold = float(args.pop(0))
            except ValueError:
                pass
        else:
            pass  # Ignore unknown flags — fail to passive

    # Determine input source
    if not args or args[0] == "-":
        entries = read_jsonl(sys.stdin)
    else:
        try:
            with open(args[0], "r") as f:  # noqa: S104
                entries = read_jsonl(f)
        except (OSError, IOError):
            # Fail to passive: can't read input = no alerts
            sys.exit(0)

    if not entries:
        # No data = no alerts
        sys.exit(0)

    alerts = analyze(entries, config)

    if config.dry_run:
        summary = {
            "weapon": "S9-W-001",
            "mode": "dry_run",
            "entries_analyzed": len(entries),
            "alerts_generated": len(alerts),
            "by_type": {},
        }
        for a in alerts:
            t = a["alert_type"]
            summary["by_type"][t] = summary["by_type"].get(t, 0) + 1
        print(json.dumps(summary, indent=2))
    else:
        for alert in alerts:
            print(json.dumps(alert))


if __name__ == "__main__":
    main()

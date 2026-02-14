"""
Sample SAIF v1.1 Artifact: Key-Value Counter
Demonstrates the three mandatory functions: ingest, compact, audit.

This artifact maintains a simple key-value store with counters.
It tracks how many times each key has been written, preserves
total event count as an invariant, and compacts by keeping only
the top-N keys by frequency.

Use this as a starting template for your own artifacts.
"""


def ingest(event_payload: dict, state: dict) -> tuple:
    """
    Process an incoming event, return (new_state, lineage_item).

    This implementation:
    - Stores the latest value for each key
    - Counts writes per key
    - Maintains a total event counter as an invariant
    """
    key = event_payload.get("key", "")
    value = event_payload.get("value", "")

    # Initialize state structure on first call
    if "keys" not in state:
        state = {"keys": {}, "total_events": 0, "_version": 1}

    # Update key store
    keys = dict(state.get("keys", {}))
    if key not in keys:
        keys[key] = {"value": value, "writes": 1}
    else:
        keys[key] = {
            "value": value,
            "writes": keys[key].get("writes", 0) + 1,
        }

    total = state.get("total_events", 0) + 1

    new_state = {
        "keys": keys,
        "total_events": total,
        "_version": state.get("_version", 1),
    }

    lineage_item = {
        "action": "ingest",
        "key": key,
        "event_number": total,
    }

    return (new_state, lineage_item)


def compact(state: dict, lineage: list, target_bytes: int) -> dict:
    """
    Compress state to fit within target_bytes without losing invariants.

    Strategy: keep the top-N most-written keys until we fit.
    The total_events counter is NEVER dropped — it's our invariant.
    """
    import json

    keys = state.get("keys", {})
    total = state.get("total_events", 0)
    version = state.get("_version", 1)

    # Sort keys by write count (most written first)
    sorted_keys = sorted(keys.items(), key=lambda x: x[1].get("writes", 0), reverse=True)

    # Progressively drop least-written keys until we fit
    kept = dict(sorted_keys)
    while sorted_keys:
        candidate = {
            "keys": kept,
            "total_events": total,
            "_version": version,
            "_compacted": True,
            "_keys_before": len(keys),
            "_keys_after": len(kept),
        }
        size = len(json.dumps(candidate, sort_keys=True).encode("utf-8"))
        if size <= target_bytes:
            return candidate
        # Drop the least-written key
        if sorted_keys:
            sorted_keys.pop()
            kept = dict(sorted_keys)

    # Absolute minimum: just the invariant
    return {
        "keys": {},
        "total_events": total,
        "_version": version,
        "_compacted": True,
        "_keys_before": len(keys),
        "_keys_after": 0,
    }


def audit(state: dict, lineage: list):
    """
    Self-check. Returns 'OK' or ('HALT', reason).

    Checks:
    1. total_events must exist and be non-negative
    2. total_events must be >= number of lineage entries
    3. All keys must have positive write counts
    4. _version must exist
    """
    # Check invariant: total_events
    total = state.get("total_events")
    if total is None:
        return ("HALT", "Missing total_events invariant")
    if not isinstance(total, int) or total < 0:
        return ("HALT", f"Invalid total_events: {total}")

    # Check lineage consistency (after compaction, lineage may be truncated)
    if lineage and total < len(lineage):
        return ("HALT", f"total_events ({total}) < lineage length ({len(lineage)})")

    # Check key integrity
    keys = state.get("keys", {})
    for k, v in keys.items():
        writes = v.get("writes", 0)
        if writes <= 0:
            return ("HALT", f"Key '{k}' has non-positive writes: {writes}")

    # Check version
    if "_version" not in state:
        return ("HALT", "Missing _version field")

    return "OK"

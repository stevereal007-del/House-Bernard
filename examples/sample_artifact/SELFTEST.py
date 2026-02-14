"""SAIF v1.1 Self-Test for Key-Value Counter artifact."""
import json
import mutation


def run_selftest():
    state = {}
    lineage = []

    # Ingest 20 events
    for i in range(20):
        event = {"key": f"key_{i % 5}", "value": f"val_{i}"}
        state, item = mutation.ingest(event, state)
        lineage.append(item)

    # Audit should pass
    result = mutation.audit(state, lineage)
    assert result == "OK", f"Audit failed after ingest: {result}"
    assert state["total_events"] == 20, f"Wrong total: {state['total_events']}"
    assert len(state["keys"]) == 5, f"Wrong key count: {len(state['keys'])}"

    # Compact to small size
    compacted = mutation.compact(state, lineage, 200)
    result2 = mutation.audit(compacted, lineage)
    assert result2 == "OK", f"Audit failed after compact: {result2}"
    assert compacted["total_events"] == 20, "Invariant lost in compaction"

    print("SELFTEST: ALL CHECKS PASSED")
    return True


if __name__ == "__main__":
    run_selftest()

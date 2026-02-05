#!/usr/bin/env python3
"""
LAB A PHASE 0 EXECUTIONER - PRODUCTION GRADE
ASCII-clean, deterministic, hostile-by-default.

SAIF v1.1 Contract (FROZEN):

- ingest(event_payload: dict, state: dict) -> (new_state: dict, lineage_item: dict)
- compact(state: dict, lineage: list, target_bytes: int) -> new_state: dict
- audit(state: dict, lineage: list) -> "OK" or ("HALT", reason: str)

Tests:
- T0: SELFTEST (in Docker)
- T1: Syntax/Import (host compile + Docker import)
- T2: Degradation (progressive ledger truncation)
- T3: Compaction (forced target_bytes + audit)
- T4: Restart (persistent /work across container runs)

Dies at first failure. No partial credit.
"""

import subprocess
import hashlib
import json
import shutil
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, Optional, Set, List


# NOTE: Pin this to a digest after pulling on the Beelink:
# docker pull python:3.10.15-alpine
# docker image inspect python:3.10.15-alpine --format '{{.RepoDigests}}'
DOCKER_IMAGE = "python:3.10.15-alpine"


SAIF_RUNNER = """#!/usr/bin/env python3
import sys
import json
from pathlib import Path

# Load mutation from /app (read-only)
sys.path.insert(0, "/app")
import mutation  # noqa

command = sys.argv[1] if len(sys.argv) > 1 else "audit"

work = Path("/work")
state_file = work / "state.json"
ledger_file = work / "ledger.jsonl"

if state_file.exists():
    with open(state_file, "r", encoding="utf-8") as f:
        state = json.load(f)
else:
    state = {}

def load_lineage(path: Path):
    lineage = []
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                lineage.append(json.loads(line))
    return lineage

if command == "ingest":
    # Deterministic events: 100 writes, 10 keys cycled
    for i in range(100):
        event = {"key": f"key_{i % 10}", "value": f"value_{i}"}
        new_state, lineage_item = mutation.ingest(event, state)
        state = new_state
        # lineage_item MUST be JSON-serializable
        with open(ledger_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(lineage_item, sort_keys=True) + "\\n")

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, sort_keys=True)

    print("OK")
    sys.exit(0)

elif command == "compact":
    lineage = load_lineage(ledger_file)
    target = int(sys.argv[2]) if len(sys.argv) > 2 else 5000

    # Contract: compact(state, lineage, target_bytes:int) -> new_state
    new_state = mutation.compact(state, lineage, target)

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(new_state, f, sort_keys=True)

    print("OK")
    sys.exit(0)

elif command == "audit":
    lineage = load_lineage(ledger_file)

    # Contract: audit(state, lineage) -> "OK" or ("HALT", reason)
    result = mutation.audit(state, lineage)

    if isinstance(result, tuple) and len(result) == 2:
        status, reason = result
        if status == "HALT":
            print(f"HALT: {reason}")
            sys.exit(1)

    if result != "OK" and result is not None:
        # Allow "OK" or None. Anything else is suspicious but not fatal unless you want it to be.
        pass

    print("OK")
    sys.exit(0)

else:
    print(f"HALT: Unknown command '{command}'")
    sys.exit(1)
"""


class ExecutionerProduction:
    def __init__(self):
        self.results = Path.home() / ".openclaw" / "lab_a" / "results"
        self.survivors = Path.home() / ".openclaw" / "lab_a" / "survivors"
        self.results.mkdir(parents=True, exist_ok=True)
        self.survivors.mkdir(parents=True, exist_ok=True)

        # Deterministic schedules
        self.degradation_counts: List[int] = [1000, 500, 250, 100, 50, 10]
        self.compaction_bytes: List[int] = [8000, 5000, 3000, 1000]
        self.restart_cycles: int = 5

        # Phase 0 limits
        self.work_size_limit: int = 16 * 1024 * 1024  # 16MB

        self.failure_cache: Set[str] = self._load_failures()

    # -------------------------
    # Public entry
    # -------------------------
    def execute(self, zip_path: Path) -> Dict:
        artifact_hash = self._hash(zip_path)

        if artifact_hash in self.failure_cache:
            return {"verdict": "DUPLICATE_FAILURE", "hash": artifact_hash}

        event_id = self._next_event()
        result: Dict = {
            "event_id": event_id,
            "artifact": zip_path.name,
            "hash": artifact_hash,
            "tests": {},
        }

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)

            # Extract
            try:
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(temp_path)
            except Exception as e:
                result["verdict"] = "KILLED_INVALID_ZIP"
                result["error"] = str(e)
                self._kill(zip_path, result)
                return result

            saif_root = self._resolve_root(temp_path)

            validation = self._validate_saif(saif_root)
            if not validation["valid"]:
                result["verdict"] = "KILLED_INVALID_SAIF"
                result["error"] = validation["error"]
                self._kill(zip_path, result)
                return result

            # Work dir for T0/T1
            work = temp_path / "work"
            work.mkdir(exist_ok=True)

            # T0: SELFTEST (Docker-only)
            if not self._t0_selftest(saif_root, work):
                result["verdict"] = "KILLED_T0_SELFTEST"
                self._kill(zip_path, result)
                return result
            result["tests"]["t0"] = "PASS"

            # T1: Syntax (host compile) + Docker import test
            t1 = self._t1_syntax(saif_root, work)
            if not t1["success"]:
                result["verdict"] = "KILLED_T1_SYNTAX"
                result["tests"]["t1"] = t1
                self._kill(zip_path, result)
                return result
            result["tests"]["t1"] = t1

            # T2: Degradation
            t2 = self._t2_degradation(saif_root)
            if not t2["success"]:
                result["verdict"] = "KILLED_T2_DEGRADATION"
                result["tests"]["t2"] = t2
                self._kill(zip_path, result)
                return result
            result["tests"]["t2"] = t2

            # T3: Compaction
            t3 = self._t3_compaction(saif_root)
            if not t3["success"]:
                result["verdict"] = "KILLED_T3_COMPACTION"
                result["tests"]["t3"] = t3
                self._kill(zip_path, result)
                return result
            result["tests"]["t3"] = t3

            # T4: Restart
            t4 = self._t4_restart(saif_root)
            if not t4["success"]:
                result["verdict"] = "KILLED_T4_RESTART"
                result["tests"]["t4"] = t4
                self._kill(zip_path, result)
                return result
            result["tests"]["t4"] = t4

        result["verdict"] = "SURVIVOR_PHASE_0"
        self._promote(zip_path, result)
        return result

    # -------------------------
    # SAIF validation
    # -------------------------
    def _resolve_root(self, extracted: Path) -> Path:
        children = [
            p for p in extracted.iterdir()
            if not p.name.startswith("__MACOSX") and not p.name.startswith(".")
        ]
        if len(children) == 1 and children[0].is_dir():
            return children[0]
        return extracted

    def _validate_saif(self, root: Path) -> Dict:
        required = ["manifest.json", "schema.json", "mutation.py", "SELFTEST.py", "README.md"]
        for fname in required:
            if not (root / fname).exists():
                return {"valid": False, "error": f"Missing {fname}"}

        try:
            with open(root / "manifest.json", "r", encoding="utf-8") as f:
                manifest = json.load(f)

            iface = manifest.get("interface")
            if not isinstance(iface, dict):
                return {"valid": False, "error": "manifest.json: missing/invalid 'interface' dict"}

            for func in ["ingest", "compact", "audit"]:
                if func not in iface:
                    return {"valid": False, "error": f"manifest.json: interface missing '{func}'"}

        except Exception as e:
            return {"valid": False, "error": f"Bad manifest.json: {e}"}

        return {"valid": True}

    # -------------------------
    # Docker invocation
    # -------------------------
    def _docker_base(self, root: Path, work: Path, memory: str, cpus: str, pids: str) -> List[str]:
        return [
            "docker", "run", "--rm",
            "--network=none",
            "--memory", memory,
            "--cpus", cpus,
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt", "no-new-privileges",
            "--pids-limit", pids,
            "--user", "65534:65534",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
            "-v", f"{root}:/app:ro",
            "-v", f"{work}:/work",
            "-w", "/work",
            DOCKER_IMAGE,
        ]

    def _enforce_work_limit(self, work: Path) -> bool:
        try:
            total = 0
            for f in work.rglob("*"):
                if f.is_file():
                    total += f.stat().st_size
                    if total > self.work_size_limit:
                        return False
            return True
        except Exception:
            return False

    # -------------------------
    # Tests
    # -------------------------
    def _t0_selftest(self, root: Path, work: Path) -> bool:
        try:
            cmd = self._docker_base(root, work, memory="50m", cpus="0.25", pids="64")
            cmd += ["python3", "/app/SELFTEST.py"]
            r = subprocess.run(cmd, capture_output=True, timeout=30)
            return r.returncode == 0 and self._enforce_work_limit(work)
        except Exception:
            return False

    def _t1_syntax(self, root: Path, work: Path) -> Dict:
        # Host compile check (fast fail)
        try:
            compile_result = subprocess.run(
                ["python3", "-m", "py_compile", str(root / "mutation.py")],
                capture_output=True,
                timeout=10,
            )
            if compile_result.returncode != 0:
                return {"success": False, "stage": "compile", "stderr": compile_result.stderr.decode("utf-8", "ignore")[:500]}
        except Exception as e:
            return {"success": False, "stage": "compile", "error": str(e)[:200]}

        # Docker import test (no trust)
        try:
            import_test = work / "import_test.py"
            import_test.write_text('import sys\nsys.path.insert(0,"/app")\nimport mutation\nprint("OK")\n', encoding="utf-8")

            cmd = self._docker_base(root, work, memory="100m", cpus="0.5", pids="128")
            cmd += ["python3", "/work/import_test.py"]
            r = subprocess.run(cmd, capture_output=True, timeout=30)
            ok = (r.returncode == 0) and self._enforce_work_limit(work)
            if not ok:
                return {"success": False, "stage": "import", "stderr": r.stderr.decode("utf-8", "ignore")[:500]}
            return {"success": True}
        except Exception as e:
            return {"success": False, "stage": "import", "error": str(e)[:200]}

    def _t2_degradation(self, root: Path) -> Dict:
        baseline = Path(tempfile.mkdtemp())
        try:
            if not self._run(root, baseline, "ingest"):
                return {"success": False, "failed_at": "baseline_ingest"}

            src = baseline / "ledger.jsonl"

            for count in self.degradation_counts:
                test = Path(tempfile.mkdtemp())
                try:
                    self._truncate_ledger(src, test / "ledger.jsonl", count)
                    # No state.json on purpose: this simulates cold-start + partial history
                    if not self._run(root, test, "audit"):
                        return {"success": False, "failed_at": f"{count}_events"}
                finally:
                    shutil.rmtree(test, ignore_errors=True)

            return {"success": True, "tested": self.degradation_counts}
        finally:
            shutil.rmtree(baseline, ignore_errors=True)

    def _t3_compaction(self, root: Path) -> Dict:
        baseline = Path(tempfile.mkdtemp())
        try:
            if not self._run(root, baseline, "ingest"):
                return {"success": False, "failed_at": "baseline_ingest"}

            for target in self.compaction_bytes:
                test = Path(tempfile.mkdtemp())
                try:
                    shutil.copy(baseline / "state.json", test / "state.json")
                    shutil.copy(baseline / "ledger.jsonl", test / "ledger.jsonl")

                    if not self._run(root, test, "compact", str(target)):
                        return {"success": False, "failed_at": f"{target}b", "stage": "compact"}

                    if not self._run(root, test, "audit"):
                        return {"success": False, "failed_at": f"{target}b", "stage": "audit"}

                finally:
                    shutil.rmtree(test, ignore_errors=True)

            return {"success": True, "tested": self.compaction_bytes}
        finally:
            shutil.rmtree(baseline, ignore_errors=True)

    def _t4_restart(self, root: Path) -> Dict:
        work = Path(tempfile.mkdtemp())
        try:
            for cycle in range(self.restart_cycles):
                if cycle == 0:
                    if not self._run(root, work, "ingest"):
                        return {"success": False, "cycle": cycle, "stage": "ingest"}

                if not self._run(root, work, "audit"):
                    return {"success": False, "cycle": cycle, "stage": "reconstruct"}

            return {"success": True, "cycles": self.restart_cycles}
        finally:
            shutil.rmtree(work, ignore_errors=True)

    # -------------------------
    # Runner execution
    # -------------------------
    def _run(self, root: Path, work: Path, cmd: str, arg: str = "") -> bool:
        work.mkdir(parents=True, exist_ok=True)

        runner = work / "runner.py"
        runner.write_text(SAIF_RUNNER, encoding="utf-8")

        if not self._enforce_work_limit(work):
            return False

        try:
            args = ["python3", "/work/runner.py", cmd]
            if arg:
                args.append(arg)

            docker_cmd = self._docker_base(root, work, memory="100m", cpus="0.5", pids="128")
            docker_cmd += args

            r = subprocess.run(docker_cmd, capture_output=True, timeout=30)

            return (r.returncode == 0) and self._enforce_work_limit(work)
        except Exception:
            return False

    def _truncate_ledger(self, src: Path, dst: Path, max_events: int) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not src.exists():
            dst.write_text("", encoding="utf-8")
            return

        with open(src, "r", encoding="utf-8") as f:
            events = f.readlines()

        truncated = events[-max_events:] if len(events) > max_events else events

        with open(dst, "w", encoding="utf-8") as f:
            f.writelines(truncated)

    # -------------------------
    # Bookkeeping
    # -------------------------
    def _hash(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()

    def _next_event(self) -> str:
        seq = self.results / "EVENT_SEQUENCE.txt"
        if not seq.exists():
            seq.write_text("0", encoding="utf-8")
        n = int(seq.read_text(encoding="utf-8").strip() or "0")
        seq.write_text(str(n + 1), encoding="utf-8")
        return f"{n + 1:08d}"

    def _load_failures(self) -> Set[str]:
        cache = self.results / "FAILURE_FINGERPRINTS.txt"
        if not cache.exists():
            return set()
        with open(cache, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())

    def _kill(self, artifact: Path, result: Dict) -> None:
        log = self.results / "ELIMINATION_LOG.jsonl"
        with open(log, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, sort_keys=True) + "\n")

        cache = self.results / "FAILURE_FINGERPRINTS.txt"
        with open(cache, "a", encoding="utf-8") as f:
            f.write(f"{result['hash']}\n")

        self.failure_cache.add(result["hash"])

        try:
            artifact.unlink()
        except Exception:
            pass

        print(f"KILLED: {artifact.name} - {result['verdict']}")

    def _promote(self, artifact: Path, result: Dict) -> None:
        dest = self.survivors / artifact.name
        shutil.move(str(artifact), str(dest))

        log = self.results / "SURVIVOR_LOG.jsonl"
        with open(log, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, sort_keys=True) + "\n")

        print(f"SURVIVOR: {artifact.name}")


def main() -> int:
    import sys

    if len(sys.argv) < 2:
        print("Usage: executioner_production.py <artifact.zip>")
        return 1

    path = Path(sys.argv[1])
    if not path.exists() or path.suffix.lower() != ".zip":
        print("Error: Must be an existing .zip file")
        return 1

    ex = ExecutionerProduction()
    result = ex.execute(path)

    print("=" * 60)
    print(f"VERDICT: {result.get('verdict')}")
    print("=" * 60)

    return 0 if result.get("verdict") == "SURVIVOR_PHASE_0" else 1


if __name__ == "__main__":
    raise SystemExit(main())

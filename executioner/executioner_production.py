#!/usr/bin/env python3
"""
LAB A PHASE 0 EXECUTIONER - PRODUCTION GRADE
All safety issues fixed, ASCII-clean, executable

SAIF v1.1 Contract (FROZEN):
- ingest(event_payload: dict, state: dict) -> (new_state: dict, lineage_item: dict)
- compact(state: dict, lineage: list, target_bytes: int) -> new_state: dict
- audit(state: dict, lineage: list) -> "OK" or ("HALT", reason: str)
"""

import subprocess
import hashlib
import json
import shutil
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, Optional

# PINNED RUNTIME - Replace after: docker pull python:3.10.15-alpine && docker inspect
DOCKER_IMAGE = "python:3.10.15-alpine"

# SAIF Interface Runner (injected into /work, not /app)
SAIF_RUNNER = """#!/usr/bin/env python3
import sys
import json
from pathlib import Path

sys.path.insert(0, '/app')
import mutation

command = sys.argv[1] if len(sys.argv) > 1 else 'audit'

work = Path('/work')
state_file = work / 'state.json'
ledger_file = work / 'ledger.jsonl'

if state_file.exists():
    with open(state_file, 'r') as f:
        state = json.load(f)
else:
    state = {}

if command == 'ingest':
    for i in range(100):
        event = {'key': f'key_{i % 10}', 'value': f'value_{i}'}
        new_state, lineage_item = mutation.ingest(event, state)
        state = new_state
        with open(ledger_file, 'a') as f:
            f.write(json.dumps(lineage_item, sort_keys=True) + '\\n')
    with open(state_file, 'w') as f:
        json.dump(state, f, sort_keys=True)

elif command == 'compact':
    lineage = []
    if ledger_file.exists():
        with open(ledger_file, 'r') as f:
            for line in f:
                lineage.append(json.loads(line))
    target = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    new_state = mutation.compact(state, lineage, target)
    with open(state_file, 'w') as f:
        json.dump(new_state, f, sort_keys=True)

elif command == 'audit':
    lineage = []
    if ledger_file.exists():
        with open(ledger_file, 'r') as f:
            for line in f:
                lineage.append(json.loads(line))
    result = mutation.audit(state, lineage)
    if isinstance(result, tuple):
        status, reason = result
        if status == 'HALT':
            print(f'HALT: {reason}')
            sys.exit(1)
    print('OK')
"""


class ExecutionerProduction:
    def __init__(self):
        self.results = Path.home() / ".openclaw/lab_a/results"
        self.survivors = Path.home() / ".openclaw/lab_a/survivors"
        self.results.mkdir(parents=True, exist_ok=True)
        self.survivors.mkdir(parents=True, exist_ok=True)
        
        # Deterministic schedules
        self.degradation_counts = [1000, 500, 250, 100, 50, 10]
        self.compaction_bytes = [8000, 5000, 3000, 1000]
        self.restart_cycles = 5
        
        # Phase 0 limits
        self.work_size_limit = 16 * 1024 * 1024  # 16MB
        
        self.failure_cache = self._load_failures()
    
    def execute(self, zip_path: Path) -> Dict:
        artifact_hash = self._hash(zip_path)
        
        if artifact_hash in self.failure_cache:
            return {'verdict': 'DUPLICATE_FAILURE', 'hash': artifact_hash}
        
        event_id = self._next_event()
        result = {'event_id': event_id, 'artifact': zip_path.name, 
                  'hash': artifact_hash, 'tests': {}}
        
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            
            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(temp_path)
            except Exception as e:
                result['verdict'] = 'KILLED_INVALID_ZIP'
                result['error'] = str(e)
                self._kill(zip_path, result)
                return result
            
            saif_root = self._resolve_root(temp_path)
            
            validation = self._validate_saif(saif_root)
            if not validation['valid']:
                result['verdict'] = 'KILLED_INVALID_SAIF'
                result['error'] = validation['error']
                self._kill(zip_path, result)
                return result
            
            work = Path(temp) / 'work'
            work.mkdir()
            
            # T0: SELFTEST
            if not self._t0_selftest(saif_root, work):
                result['verdict'] = 'KILLED_T0_SELFTEST'
                self._kill(zip_path, result)
                return result
            result['tests']['t0'] = 'PASS'
            
            # T1: Syntax
            t1 = self._t1_syntax(saif_root, work)
            if not t1['success']:
                result['verdict'] = 'KILLED_T1_SYNTAX'
                result['tests']['t1'] = t1
                self._kill(zip_path, result)
                return result
            result['tests']['t1'] = t1
            
            # T2: Degradation
            t2 = self._t2_degradation(saif_root)
            if not t2['success']:
                result['verdict'] = 'KILLED_T2_DEGRADATION'
                result['tests']['t2'] = t2
                self._kill(zip_path, result)
                return result
            result['tests']['t2'] = t2
            
            # T3: Compaction
            t3 = self._t3_compaction(saif_root)
            if not t3['success']:
                result['verdict'] = 'KILLED_T3_COMPACTION'
                result['tests']['t3'] = t3
                self._kill(zip_path, result)
                return result
            result['tests']['t3'] = t3
            
            # T4: Restart
            t4 = self._t4_restart(saif_root)
            if not t4['success']:
                result['verdict'] = 'KILLED_T4_RESTART'
                result['tests']['t4'] = t4
                self._kill(zip_path, result)
                return result
            result['tests']['t4'] = t4
        
        result['verdict'] = 'SURVIVOR_PHASE_0'
        self._promote(zip_path, result)
        return result
    
    def _resolve_root(self, extracted: Path) -> Path:
        children = [p for p in extracted.iterdir() 
                   if not p.name.startswith('__MACOSX') 
                   and not p.name.startswith('.')]
        if len(children) == 1 and children[0].is_dir():
            return children[0]
        return extracted
    
    def _validate_saif(self, root: Path) -> Dict:
        required = ['manifest.json', 'schema.json', 'mutation.py', 
                   'SELFTEST.py', 'README.md']
        
        for f in required:
            if not (root / f).exists():
                return {'valid': False, 'error': f'Missing {f}'}
        
        try:
            with open(root / 'manifest.json') as f:
                manifest = json.load(f)
            
            if 'interface' not in manifest:
                return {'valid': False, 'error': 'No interface'}
            
            iface = manifest['interface']
            for func in ['ingest', 'compact', 'audit']:
                if func not in iface:
                    return {'valid': False, 'error': f'Missing {func}'}
        except Exception as e:
            return {'valid': False, 'error': f'Bad manifest: {e}'}
        
        return {'valid': True}
    
    def _t0_selftest(self, root: Path, work: Path) -> bool:
        try:
            result = subprocess.run([
                'docker', 'run', '--rm',
                '--network=none',
                '--memory=50m',
                '--cpus=0.25',
                '--read-only',
                '--cap-drop=ALL',
                '--security-opt', 'no-new-privileges',
                '--pids-limit', '64',
                '--user', '65534:65534',
                '--tmpfs', '/tmp:rw,noexec,nosuid,size=8m',
                '-v', f'{root}:/app:ro',
                '-v', f'{work}:/work',
                '-w', '/work',
                DOCKER_IMAGE,
                'python3', '/app/SELFTEST.py'
            ], capture_output=True, timeout=30)
            return result.returncode == 0
        except:
            return False
    
    def _t1_syntax(self, root: Path, work: Path) -> Dict:
        try:
            compile_result = subprocess.run(
                ['python3', '-m', 'py_compile', str(root / 'mutation.py')],
                capture_output=True, timeout=10)
            if compile_result.returncode != 0:
                return {'success': False, 'stage': 'compile'}
        except:
            return {'success': False, 'stage': 'compile'}
        
        try:
            test_script = work / 'import_test.py'
            test_script.write_text('import mutation\nprint("OK")')
            
            result = subprocess.run([
                'docker', 'run', '--rm',
                '--network=none',
                '--memory=100m',
                '--cpus=0.5',
                '--read-only',
                '--cap-drop=ALL',
                '--security-opt', 'no-new-privileges',
                '--pids-limit', '128',
                '--user', '65534:65534',
                '--tmpfs', '/tmp:rw,noexec,nosuid,size=16m',
                '-v', f'{root}:/app:ro',
                '-v', f'{work}:/work',
                '-w', '/work',
                DOCKER_IMAGE,
                'python3', 'import_test.py'
            ], capture_output=True, timeout=30)
            
            return {'success': result.returncode == 0}
        except:
            return {'success': False, 'stage': 'import'}
    
    def _t2_degradation(self, root: Path) -> Dict:
        baseline_work = Path(tempfile.mkdtemp())
        self._run(root, baseline_work, 'ingest')
        
        for count in self.degradation_counts:
            test_work = Path(tempfile.mkdtemp())
            self._truncate_ledger(baseline_work / 'ledger.jsonl',
                                 test_work / 'ledger.jsonl', count)
            
            if not self._run(root, test_work, 'audit'):
                shutil.rmtree(baseline_work)
                shutil.rmtree(test_work)
                return {'success': False, 'failed_at': f'{count}_events'}
            
            shutil.rmtree(test_work)
        
        shutil.rmtree(baseline_work)
        return {'success': True, 'tested': self.degradation_counts}
    
    def _t3_compaction(self, root: Path) -> Dict:
        baseline = Path(tempfile.mkdtemp())
        self._run(root, baseline, 'ingest')
        
        for target in self.compaction_bytes:
            test = Path(tempfile.mkdtemp())
            shutil.copy(baseline / 'state.json', test / 'state.json')
            shutil.copy(baseline / 'ledger.jsonl', test / 'ledger.jsonl')
            
            if not self._run(root, test, 'compact', str(target)):
                shutil.rmtree(baseline)
                shutil.rmtree(test)
                return {'success': False, 'failed_at': f'{target}b', 
                       'stage': 'compact'}
            
            if not self._run(root, test, 'audit'):
                shutil.rmtree(baseline)
                shutil.rmtree(test)
                return {'success': False, 'failed_at': f'{target}b',
                       'stage': 'audit'}
            
            shutil.rmtree(test)
        
        shutil.rmtree(baseline)
        return {'success': True, 'tested': self.compaction_bytes}
    
    def _t4_restart(self, root: Path) -> Dict:
        work = Path(tempfile.mkdtemp())
        
        for cycle in range(self.restart_cycles):
            if cycle == 0:
                if not self._run(root, work, 'ingest'):
                    shutil.rmtree(work)
                    return {'success': False, 'cycle': cycle, 'stage': 'ingest'}
            
            if not self._run(root, work, 'audit'):
                shutil.rmtree(work)
                return {'success': False, 'cycle': cycle, 'stage': 'reconstruct'}
        
        shutil.rmtree(work)
        return {'success': True, 'cycles': self.restart_cycles}
    
    def _run(self, root: Path, work: Path, cmd: str, arg: str = '') -> bool:
        runner = work / 'runner.py'
        runner.write_text(SAIF_RUNNER)
        
        size = sum(f.stat().st_size for f in work.rglob('*') if f.is_file())
        if size > self.work_size_limit:
            print(f'[WORK_LIMIT] Exceeded {self.work_size_limit} bytes')
            return False
        
        try:
            args = ['python3', 'runner.py', cmd]
            if arg:
                args.append(arg)
            
            result = subprocess.run([
                'docker', 'run', '--rm',
                '--network=none',
                '--memory=100m',
                '--cpus=0.5',
                '--read-only',
                '--cap-drop=ALL',
                '--security-opt', 'no-new-privileges',
                '--pids-limit', '128',
                '--user', '65534:65534',
                '--tmpfs', '/tmp:rw,noexec,nosuid,size=16m',
                '-v', f'{root}:/app:ro',
                '-v', f'{work}:/work',
                '-w', '/work',
                DOCKER_IMAGE,
                *args
            ], capture_output=True, timeout=30)
            
            return result.returncode == 0
        except:
            return False
    
    def _truncate_ledger(self, src: Path, dst: Path, max_events: int):
        if not src.exists():
            dst.touch()
            return
        
        with open(src) as f:
            events = [line for line in f]
        
        truncated = events[-max_events:] if len(events) > max_events else events
        
        with open(dst, 'w') as f:
            for event in truncated:
                f.write(event)
    
    def _hash(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                h.update(chunk)
        return h.hexdigest()
    
    def _next_event(self) -> str:
        seq = self.results / 'EVENT_SEQUENCE.txt'
        if not seq.exists():
            seq.write_text('0')
        n = int(seq.read_text())
        seq.write_text(str(n + 1))
        return f'{n + 1:08d}'
    
    def _load_failures(self) -> set:
        cache = self.results / 'FAILURE_FINGERPRINTS.txt'
        if not cache.exists():
            return set()
        with open(cache) as f:
            return set(line.strip() for line in f)
    
    def _kill(self, artifact: Path, result: Dict):
        log = self.results / 'ELIMINATION_LOG.jsonl'
        with open(log, 'a') as f:
            f.write(json.dumps(result, sort_keys=True) + '\n')
        
        cache = self.results / 'FAILURE_FINGERPRINTS.txt'
        with open(cache, 'a') as f:
            f.write(f"{result['hash']}\n")
        
        self.failure_cache.add(result['hash'])
        artifact.unlink()
        print(f"KILLED: {artifact.name} - {result['verdict']}")
    
    def _promote(self, artifact: Path, result: Dict):
        dest = self.survivors / artifact.name
        shutil.move(str(artifact), str(dest))
        
        log = self.results / 'SURVIVOR_LOG.jsonl'
        with open(log, 'a') as f:
            f.write(json.dumps(result, sort_keys=True) + '\n')
        
        print(f"SURVIVOR: {artifact.name}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: executioner_production.py <artifact.zip>")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    if not path.exists() or path.suffix != '.zip':
        print("Error: Must be existing .zip file")
        sys.exit(1)
    
    ex = ExecutionerProduction()
    result = ex.execute(path)
    
    print("=" * 60)
    print(f"VERDICT: {result['verdict']}")
    print("=" * 60)
    
    sys.exit(0 if result['verdict'] == 'SURVIVOR_PHASE_0' else 1)

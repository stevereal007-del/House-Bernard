#!/usr/bin/env python3
"""
Airlock Monitor - Lab A Phase 0
Watches inbox, runs security scanner, then triggers executioner on clean artifacts.

F2 FIX: Security scanner runs before executioner. REJECT/QUARANTINE → quarantine dir.
F9 FIX: Paths resolved relative to repo root, not hardcoded to home directory.
"""

import json
import shutil
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# Resolve paths relative to this file's location in the repo
REPO_ROOT = Path(__file__).resolve().parent.parent
EXECUTIONER = REPO_ROOT / "executioner" / "executioner_production.py"
SECURITY_SCANNER = REPO_ROOT / "security" / "security_scanner.py"


class AirlockHandler(FileSystemEventHandler):
    def __init__(self, sandbox: Path, quarantine: Path):
        self.sandbox = sandbox
        self.quarantine = quarantine
        self.sandbox.mkdir(parents=True, exist_ok=True)
        self.quarantine.mkdir(parents=True, exist_ok=True)

    def _wait_for_stable(self, path: Path, timeout: float = 10.0, interval: float = 1.0) -> bool:
        """Wait until file size is stable (write complete). Returns False on timeout."""
        prev_size = -1
        elapsed = 0.0
        while elapsed < timeout:
            try:
                curr_size = path.stat().st_size
            except OSError:
                return False
            if curr_size == prev_size and curr_size > 0:
                return True
            prev_size = curr_size
            time.sleep(interval)
            elapsed += interval
        return False

    def _run_security_scan(self, artifact_dir: Path) -> str:
        """Run security scanner on extracted artifact. Returns verdict: PASS, REJECT, QUARANTINE."""
        if not SECURITY_SCANNER.exists():
            print('[AIRLOCK] WARNING: Security scanner not found, defaulting to QUARANTINE')
            return "QUARANTINE"

        try:
            result = subprocess.run(
                ['python3', str(SECURITY_SCANNER), '--scan-dir', str(artifact_dir)],
                capture_output=True, text=True, timeout=60,
            )

            # Parse JSON output for overall_verdict
            try:
                scan_result = json.loads(result.stdout)
                return scan_result.get("overall_verdict", "REJECT")
            except (json.JSONDecodeError, ValueError):
                # Fall back to exit code
                if result.returncode == 0:
                    return "PASS"
                return "REJECT"

        except subprocess.TimeoutExpired:
            print('[AIRLOCK] Security scan timed out')
            return "QUARANTINE"
        except Exception as e:
            print(f'[AIRLOCK] Security scan error: {e}')
            return "QUARANTINE"

    def on_created(self, event):
        if event.is_directory:
            return

        artifact = Path(event.src_path)

        # Only process .zip files
        if artifact.suffix != '.zip':
            print(f'[AIRLOCK] Ignoring non-zip: {artifact.name}')
            return

        print(f'[AIRLOCK] New artifact detected: {artifact.name}')

        # Wait for file write to complete before moving
        if not self._wait_for_stable(artifact):
            print(f'[AIRLOCK] File not stable after timeout, skipping: {artifact.name}')
            return

        # Move to sandbox
        dest = self.sandbox / artifact.name
        try:
            shutil.move(str(artifact), str(dest))
            print(f'[AIRLOCK] Moved to sandbox: {dest}')
        except Exception as e:
            print(f'[AIRLOCK] Failed to move: {e}')
            return

        # --- F2: Security scan BEFORE executioner ---
        # Extract zip to temp dir for scanning (scanner needs .py files, not .zip)
        scan_dir = None
        try:
            scan_dir = Path(tempfile.mkdtemp(prefix="airlock_scan_"))
            with zipfile.ZipFile(str(dest), 'r') as zf:
                zf.extractall(scan_dir)
            print(f'[AIRLOCK] Running security scan...')
            scan_verdict = self._run_security_scan(scan_dir)
        except Exception as e:
            print(f'[AIRLOCK] Failed to extract for scanning: {e}')
            scan_verdict = "QUARANTINE"
        finally:
            if scan_dir and scan_dir.exists():
                shutil.rmtree(scan_dir, ignore_errors=True)

        if scan_verdict == "REJECT":
            print(f'[AIRLOCK] REJECTED by security scanner: {artifact.name}')
            quarantine_dest = self.quarantine / artifact.name
            try:
                shutil.move(str(dest), str(quarantine_dest))
            except Exception:
                pass
            return

        if scan_verdict == "QUARANTINE":
            print(f'[AIRLOCK] QUARANTINED by security scanner: {artifact.name}')
            quarantine_dest = self.quarantine / artifact.name
            try:
                shutil.move(str(dest), str(quarantine_dest))
            except Exception:
                pass
            return

        # PASS or FLAG - proceed to executioner
        if scan_verdict == "FLAG":
            print(f'[AIRLOCK] Security scan flagged (low-severity), proceeding: {artifact.name}')
        print(f'[AIRLOCK] Security scan PASSED, executing harness...')
        try:
            result = subprocess.run([
                'python3',
                str(EXECUTIONER),
                str(dest)
            ], capture_output=True, text=True, timeout=300)

            # Extract verdict from output
            output = result.stdout
            if 'VERDICT:' in output:
                verdict = output.split('VERDICT:')[1].split('\n')[0].strip()
                print(f'[AIRLOCK] {artifact.name} -> {verdict}')
            else:
                print(f'[AIRLOCK] Execution completed (no verdict found)')

        except subprocess.TimeoutExpired:
            print(f'[AIRLOCK] Timeout (>5min) - killing test')
        except Exception as e:
            print(f'[AIRLOCK] Execution error: {e}')


def main():
    import sys

    if not EXECUTIONER.exists():
        print(f'Error: Executioner not found at {EXECUTIONER}')
        sys.exit(1)

    # Runtime directories (outside repo)
    inbox = Path.home() / '.openclaw/inbox'
    sandbox = Path.home() / '.openclaw/sandbox'
    quarantine = Path.home() / '.openclaw/quarantine'
    inbox.mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print('AIRLOCK MONITOR - Lab A Phase 0')
    print('=' * 60)
    print(f'Watching:    {inbox}')
    print(f'Sandbox:     {sandbox}')
    print(f'Quarantine:  {quarantine}')
    print(f'Executioner: {EXECUTIONER}')
    print(f'Scanner:     {SECURITY_SCANNER}')
    print('Waiting for SAIF artifacts (.zip files)...')
    print('=' * 60)

    # Start watching
    observer = Observer()
    handler = AirlockHandler(sandbox, quarantine)
    observer.schedule(handler, str(inbox), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\n[AIRLOCK] Shutting down...')
        observer.stop()

    observer.join()


if __name__ == '__main__':
    main()

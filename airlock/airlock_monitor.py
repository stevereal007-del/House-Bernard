#!/usr/bin/env python3
"""
Airlock Monitor - Lab A Phase 0
Watches inbox, triggers executioner on new SAIF artifacts
"""

import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import shutil

class AirlockHandler(FileSystemEventHandler):
    def __init__(self, executioner_path: Path):
        self.executioner = executioner_path
        self.sandbox = Path.home() / '.openclaw/sandbox'
        self.sandbox.mkdir(parents=True, exist_ok=True)
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        artifact = Path(event.src_path)
        
        # Only process .zip files
        if artifact.suffix != '.zip':
            print(f'[AIRLOCK] Ignoring non-zip: {artifact.name}')
            return
        
        print(f'[AIRLOCK] New artifact detected: {artifact.name}')
        
        # Move to sandbox
        dest = self.sandbox / artifact.name
        try:
            shutil.move(str(artifact), str(dest))
            print(f'[AIRLOCK] Moved to sandbox: {dest}')
        except Exception as e:
            print(f'[AIRLOCK] Failed to move: {e}')
            return
        
        # Trigger executioner
        print(f'[AIRLOCK] Executing harness...')
        try:
            result = subprocess.run([
                'python3',
                str(self.executioner),
                str(dest)
            ], capture_output=True, text=True, timeout=300)
            
            # Extract verdict from output
            output = result.stdout
            if 'VERDICT:' in output:
                verdict = output.split('VERDICT:')[1].split('\n')[0].strip()
                print(f'[AIRLOCK] {artifact.name} → {verdict}')
            else:
                print(f'[AIRLOCK] Execution completed (no verdict found)')
                
        except subprocess.TimeoutExpired:
            print(f'[AIRLOCK] Timeout (>5min) - killing test')
        except Exception as e:
            print(f'[AIRLOCK] Execution error: {e}')


def main():
    import sys
    
    # Path to executioner
    executioner_path = Path.home() / 'house-bernard/executioner/executioner_production.py'
    
    if not executioner_path.exists():
        print(f'Error: Executioner not found at {executioner_path}')
        print('Expected location: ~/house-bernard/executioner/executioner_production.py')
        sys.exit(1)
    
    # Inbox directory
    inbox = Path.home() / '.openclaw/inbox'
    inbox.mkdir(parents=True, exist_ok=True)
    
    print('='*60)
    print('AIRLOCK MONITOR - Lab A Phase 0')
    print('='*60)
    print(f'Watching: {inbox}')
    print(f'Executioner: {executioner_path}')
    print('Waiting for SAIF artifacts (.zip files)...')
    print('='*60)
    
    # Start watching
    observer = Observer()
    handler = AirlockHandler(executioner_path)
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

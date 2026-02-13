# Airlock - Intake Monitor

Watches for new SAIF artifacts and triggers the executioner.

## What It Does

1. Monitors `~/.openclaw/inbox/` for new .zip files
2. Moves artifacts to `~/.openclaw/sandbox/`
3. Calls executioner on each artifact
4. Logs verdicts

## Installation
```bash
pip3 install watchdog
```

## Usage
```bash
python3 airlock_monitor.py
```

Runs continuously. Press Ctrl+C to stop.

## Test It

In another terminal:
```bash
cp test_artifact.zip ~/.openclaw/inbox/
```

Watch the airlock terminal for output.

## Systemd Service (Optional)

Run as background service:
```bash
sudo cp airlock.service /etc/systemd/system/
sudo systemctl enable airlock
sudo systemctl start airlock
```

Check status:
```bash
sudo systemctl status airlock
```

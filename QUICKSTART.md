# House Bernard — Quick Start (Phase 0)

Get Lab A Phase 0 running in under 30 minutes.

## Prerequisites

- Ubuntu/Linux machine (Beelink EQ13 recommended)
- Docker installed
- Python 3.10+
- 16 GB RAM minimum

## Installation

### 1. Clone Repository

```bash
cd ~
git clone <CLASSIFIED_REPO_URL> House-Bernard
cd House-Bernard
```

### 2. Install Dependencies

```bash
# Docker
sudo apt install -y docker.io
sudo usermod -aG docker $USER
newgrp docker

# Python packages
pip3 install watchdog --break-system-packages
```

### 3. Create Runtime Directories

```bash
mkdir -p ~/.openclaw/lab_a/{results,survivors}
mkdir -p ~/.openclaw/{inbox,sandbox,purgatory,quarantine,nullsink}
```

### 4. Pull and Pin Docker Image

```bash
docker pull python:3.10.15-alpine

# Get digest and update executioner_production.py DOCKER_IMAGE constant
docker inspect --format='{{index .RepoDigests 0}}' python:3.10.15-alpine
```

### 5. Start Airlock Monitor

```bash
cd ~/House-Bernard/airlock
python3 airlock_monitor.py
```

Leave running in a terminal (or install the systemd service: `airlock/airlock.service`).

### 6. Submit a SAIF Artifact

In another terminal, create a valid SAIF v1.1 artifact (a `.zip` containing `manifest.json`, `schema.json`, `mutation.py`, `SELFTEST.py`, and `README.md` per the SAIF v1.1 contract), then drop it in the inbox:

```bash
cp my_artifact.zip ~/.openclaw/inbox/
```

> **Note:** No pre-built test artifact is shipped with the repo. See `executioner/README.md` for the required file structure.

### 7. Watch the Results

The airlock will detect the artifact, move it to sandbox, run the Executioner (T0–T4), and log the verdict.

```bash
# View logs
cat ~/.openclaw/lab_a/results/ELIMINATION_LOG.jsonl
cat ~/.openclaw/lab_a/results/SURVIVOR_LOG.jsonl

# Check for survivors
ls ~/.openclaw/lab_a/survivors/
```

### 8. Run All Tests

```bash
cd ~/House-Bernard
python3 run_tests.py
```

## Phase 0 Complete When

- One survivor passes T0–T4
- One gene extracted and documented in `ledger/GENE_REGISTRY.md`
- System runs deterministically
- No security incidents
- All test suites pass (`run_tests.py`)

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Docker permission denied | `sudo usermod -aG docker $USER && newgrp docker` |
| Executioner not found | Verify `executioner/executioner_production.py` exists |
| No module 'watchdog' | `pip3 install watchdog --break-system-packages` |
| CAA tests fail with import error | Run from repo root: `python3 caa/test_caa.py` |

## Next Steps

After first survivor: extract gene → document in ledger → plan Phase 1 (expanded adversarial testing, Splicer integration).

# House Bernard - Quick Start (Phase 0)

Get Lab A Phase 0 running in under 30 minutes.

## Prerequisites

- Ubuntu/Linux machine (Beelink EQ13 recommended)
- Docker installed
- Python 3.10+
- 16GB RAM minimum

## Installation

### 1. Clone Repository
```bash
cd ~
git clone https://github.com/stevereal007-del/House-Bernard.git
cd House-Bernard
```

### 2. Install Dependencies
```bash
# Docker
sudo apt install -y docker.io
sudo usermod -aG docker $USER
newgrp docker

# Python packages
pip3 install watchdog
```

### 3. Setup Directories
```bash
mkdir -p ~/.openclaw/lab_a/{results,survivors}
mkdir -p ~/.openclaw/{inbox,sandbox}
```

### 4. Pull Docker Image
```bash
docker pull python:3.10.15-alpine

# Get digest and update executioner_production.py line 22
docker inspect --format='{{index .RepoDigests 0}}' python:3.10.15-alpine
```

### 5. Start Airlock Monitor
```bash
cd ~/House-Bernard/airlock
python3 airlock_monitor.py
```

Leave this running in one terminal.

### 6. Submit a SAIF Artifact

In another terminal, create a valid SAIF artifact (a `.zip` containing
`manifest.json`, `schema.json`, `mutation.py`, `SELFTEST.py`, and `README.md`
per the SAIF v1.1 contract), then drop it in the inbox:
```bash
# Create your SAIF artifact as my_artifact.zip, then:
cp my_artifact.zip ~/.openclaw/inbox/
```

> **Note:** No pre-built test artifact is shipped with the repo.
> See `executioner/README.md` for the required SAIF v1.1 file structure.

### 7. Watch the Magic

The airlock will:
1. Detect the artifact
2. Move it to sandbox
3. Run executioner (T0-T4)
4. Log verdict

### 8. Check Results
```bash
# View logs
cat ~/.openclaw/lab_a/results/ELIMINATION_LOG.jsonl
cat ~/.openclaw/lab_a/results/SURVIVOR_LOG.jsonl

# Check for survivors
ls ~/.openclaw/lab_a/survivors/
```

## Expected Phase 0 Outcome

- **First 10 artifacts:** Probably all KILLED
- **Next 10 artifacts:** Maybe 1-2 SURVIVORS
- **First survivor:** Extract gene → Document in ledger
- **Foundation proven:** Phase 0 complete

## Troubleshooting

**"Docker permission denied"**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

**"Executioner not found"**
```bash
# Make sure you're in the right directory
cd ~/House-Bernard
ls executioner/executioner_production.py
```

**"No module named 'watchdog'"**
```bash
pip3 install watchdog
```

## Next Steps

After first survivor:
1. Analyze mutation.py
2. Extract gene pattern
3. Document in `ledger/GENE_REGISTRY.md`
4. Plan integration
5. Celebrate! 🎉

## Phase 0 Complete When:

✅ One survivor passes T0-T4  
✅ One gene extracted and documented  
✅ System runs deterministically  
✅ No security incidents  

Then: Plan Phase 1 (expanded adversarial testing, Splicer integration)

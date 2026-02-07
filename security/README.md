# Security

Pre-execution analysis tools and containment profiles.

## Contents

| File | Purpose |
|------|---------|
| `security_scanner.py` | AST-based static analysis of SAIF artifacts. Runs before Executioner. |
| `seccomp_lab_a.json` | Seccomp profile for Lab A containers. Standard lockdown (silent deny). |
| `seccomp_lab_b.json` | Seccomp profile for Lab B containers. Permissive logging (observe escape attempts). |

## Usage

```bash
# Scan a single file
python3 security_scanner.py artifact/mutation.py

# Scan a directory
python3 security_scanner.py --scan-dir artifact/

# Apply seccomp profile to Docker container
docker run --security-opt seccomp=seccomp_lab_a.json ...
```

## Verdicts

| Verdict | Meaning | Action |
|---------|---------|--------|
| PASS | No threats detected | Proceed to Executioner |
| FLAG | Low-severity findings | Proceed with logging |
| QUARANTINE | High-severity finding | Manual review required |
| REJECT | Critical threats or parse error | Do not execute |

---

*House Bernard — Trust Nothing, Verify Everything*

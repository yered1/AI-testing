#!/usr/bin/env bash
set -euo pipefail
python3 scripts/repo_doctor_v142.py | tee repo_audit_v142.json
echo "Wrote repo_audit_v142.json"

#!/usr/bin/env bash
set -euo pipefail
python3 scripts/repo_doctor_v141.py | tee repo_audit_v141.json

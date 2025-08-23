#!/usr/bin/env bash
set -euo pipefail
# Removes only cache/temp files; no features or sources touched.
python3 scripts/repo_doctor.py --apply-safe || python scripts/repo_doctor.py --apply-safe
echo "Safe cleanup complete."

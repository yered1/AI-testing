#!/usr/bin/env bash
set -euo pipefail
python3 scripts/repo_doctor.py "$@" || python scripts/repo_doctor.py "$@"

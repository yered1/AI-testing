#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.."; pwd)"
echo "Cleaning macOS junk and Python caches under $ROOT"
find "$ROOT" -name '__MACOSX' -type d -prune -exec rm -rf {} + || true
find "$ROOT" -name '.DS_Store' -type f -delete || true
find "$ROOT" -name '.AppleDouble' -type d -prune -exec rm -rf {} + || true
find "$ROOT" -name '__pycache__' -type d -prune -exec rm -rf {} + || true
find "$ROOT" -name '*.pyc' -type f -delete || true
find "$ROOT" -name '.pytest_cache' -type d -prune -exec rm -rf {} + || true
echo "Done."

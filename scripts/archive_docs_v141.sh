#!/usr/bin/env bash
set -euo pipefail
: "${CONFIRM:=0}"
if [ "$CONFIRM" != "1" ]; then
  echo "DRY-RUN (set CONFIRM=1 to execute)"
fi
ROOT="$(cd "$(dirname "$0")/.."; pwd)"
mkdir -p "$ROOT/docs/archive/deltas" "$ROOT/scripts/archive"
shopt -s nullglob
for f in "$ROOT"/README_DELTA_*.md; do
  echo "move $f -> docs/archive/deltas/"
  if [ "$CONFIRM" = "1" ]; then mv "$f" "$ROOT/docs/archive/deltas/"; fi
done
for f in "$ROOT"/scripts/merge_readme_v*.sh; do
  echo "move $f -> scripts/archive/"
  if [ "$CONFIRM" = "1" ]; then mv "$f" "$ROOT/scripts/archive/"; fi
done
echo "Done."

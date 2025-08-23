#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.."; pwd)"
cd "$ROOT"
READMEmd="README.md"
if [ ! -f "$READMEmd" ]; then
  echo "README.md not found in $ROOT" >&2; exit 1
fi

appended=0
for d in $(ls README_DELTA_v*.md 2>/dev/null | sort -V); do
  tag=$(grep -Eo 'Delta v[0-9]+\.[0-9]+(\.[0-9]+)?' "$d" | head -n1 || true)
  if [ -z "$tag" ]; then
    tag="$d"
  fi
  if ! grep -q "$tag" "$READMEmd"; then
    echo -e "\n\n" >> "$READMEmd"
    cat "$d" >> "$READMEmd"
    echo "Appended $d into README.md"
    appended=$((appended+1))
  else
    echo "README already contains $tag (skipping $d)"
  fi
done

if [ "$appended" -gt 0 ]; then
  echo "README consolidated with $appended delta(s)."
else
  echo "No deltas needed to append."
fi

# Delete delta files and legacy merge scripts after consolidation
rm -f README_DELTA_v*.md || true
rm -f scripts/merge_readme_v*.sh || true
echo "Removed delta files and merge scripts (if any)."

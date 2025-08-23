#!/usr/bin/env bash
set -euo pipefail
if ! grep -q "ai-testing v1.4.2 junk filters" .gitignore 2>/dev/null; then
  cat templates/gitignore.append >> .gitignore
  echo ".gitignore updated."
else
  echo ".gitignore already contains v1.4.2 filters."
fi

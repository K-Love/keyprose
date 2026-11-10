#!/usr/bin/env bash
# Build release/keyprose-release.zip from this repo.
# The zip is generated. Do not commit it.
#
# Includes tracked files and untracked files that are not gitignored.
# Drops VCS metadata, env files, databases, dependency trees, caches,
# and any zip already sitting in release/.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

OUT="${1:-$ROOT/release/keyprose-release.zip}"
mkdir -p "$(dirname "$OUT")"
rm -f "$OUT"

list="$(mktemp)"
trap 'rm -f "$list"' EXIT

git ls-files -co --exclude-standard \
  | awk '
      /(^|\/)\.env($|\.)/ { next }
      /(^|\/)\.env$/ { next }
      /\.env$/ { next }
      /\.(db|sqlite|sqlite3)$/ { next }
      /(^|\/)node_modules\// { next }
      /(^|\/)__pycache__\// { next }
      /(^|\/)\.pytest_cache\// { next }
      /(^|\/)\.mypy_cache\// { next }
      /(^|\/)\.ruff_cache\// { next }
      /(^|\/)htmlcov\// { next }
      /(^|\/)\.netlify\// { next }
      /(^|\/)netlify\/functions\/vendor\// { next }
      /(^|\/)\.venv\// { next }
      /(^|\/)venv\// { next }
      /(^|\/)\.git\// { next }
      /^\.git$/ { next }
      /^release\/.*\.zip$/ { next }
      /\.pyc$/ { next }
      /(^|\/)\.coverage$/ { next }
      { print }
    ' > "$list"

if [ ! -s "$list" ]; then
  echo "No files to archive." >&2
  exit 1
fi

zip -q -@ "$OUT" < "$list"

forbidden="$(unzip -Z1 "$OUT" | grep -E '(^|/)(\.env($|\.)|[^/]*\.env$)|(^|/)\.git(/|$)|(^|/)node_modules/|(^|/)__pycache__/|(^|/)\.pytest_cache/|(^|/)\.netlify/|(^|/)release/[^/]+\.zip$|\.(db|sqlite|sqlite3)$' || true)"
if [ -n "$forbidden" ]; then
  echo "Release zip contains an excluded path:" >&2
  echo "$forbidden" >&2
  rm -f "$OUT"
  exit 1
fi

count="$(unzip -Z1 "$OUT" | wc -l | tr -d ' ')"
echo "Wrote $OUT ($count files)"

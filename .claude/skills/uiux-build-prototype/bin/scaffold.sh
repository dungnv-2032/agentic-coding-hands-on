#!/usr/bin/env bash
# Scaffold a new grounded prototype from the skill template.
# Usage: bash bin/scaffold.sh <dest-dir> [product-name]
# Copies template/ (Vite + React + TS + Tailwind v4 + shadcn-style ui), sets the
# package name and <title>, then installs dependencies so `npm run dev` works.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:?usage: scaffold.sh <dest-dir> [product-name]}"
NAME="${2:-prototype}"

[ -e "$DEST" ] && { echo "ERROR: $DEST already exists" >&2; exit 1; }

cp -R "$SKILL_DIR/template" "$DEST"
# package name must be npm-safe; title can be anything
SLUG="$(printf '%s' "$NAME" | tr '[:upper:] ' '[:lower:]-' | tr -cd 'a-z0-9-' )"
SLUG="${SLUG:-prototype}"
perl -pi -e "s/\"name\": \"pt-prototype\"/\"name\": \"${SLUG}-prototype\"/" "$DEST/package.json"
perl -pi -e "s/<title>Prototype<\\/title>/<title>${NAME} — Prototype<\\/title>/" "$DEST/index.html"

echo "scaffolded -> $DEST"
( cd "$DEST" && npm install )
echo
echo "Next: fill pt-spec.json / src/styles/globals.css(:root tokens) / src/screens/*.tsx"
echo "Dev:  cd $DEST && npm run dev      (HMR — 編集が即反映)"
echo "Share: npm run build → dist/index.html（自己完結・開くだけ / ?switch=1 で切替FAB）"

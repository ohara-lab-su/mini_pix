#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCS="$ROOT/docs"
OUT="$DOCS/_build/html"

if [ ! -d "$ROOT/src/mini_pix" ]; then
  echo "Error: src/mini_pix is required for API documentation." >&2
  exit 1
fi

command -v sphinx-apidoc >/dev/null || { echo "Error: sphinx-apidoc is not installed." >&2; exit 1; }
command -v sphinx-build >/dev/null || { echo "Error: sphinx-build is not installed." >&2; exit 1; }

python "$DOCS/validate_docs.py"

rm -rf "$OUT"
mkdir -p "$OUT"

for LANG_CODE in en jp; do
  API_DIR="$DOCS/$LANG_CODE/api"
  mkdir -p "$API_DIR"
  sphinx-apidoc --force --module-first --output-dir "$API_DIR" "$ROOT/src/mini_pix"
done

# Build three independent HTML trees. The site root is a real Sphinx build,
# not a redirect or a copy of the English output.
DOC_LANGUAGE=en sphinx-build -b html -c "$DOCS" "$DOCS/en" "$OUT"
DOC_LANGUAGE=en sphinx-build -b html -c "$DOCS" "$DOCS/en" "$OUT/en"
DOC_LANGUAGE=ja sphinx-build -b html -c "$DOCS" "$DOCS/jp" "$OUT/jp"

if [ -f "$DOCS/_robots.txt" ]; then
  cp "$DOCS/_robots.txt" "$OUT/robots.txt"
fi

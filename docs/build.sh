#!/usr/bin/env bash
set -euo pipefail

DOCS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$DOCS_DIR/.." && pwd)"
SRC_DIR="$ROOT_DIR/src"
PKG_NAME="mini_pix"

export PYTHONPATH="$SRC_DIR:${PYTHONPATH:-}"

if [ ! -d "$SRC_DIR/$PKG_NAME" ]; then
  echo "Missing Python package: $SRC_DIR/$PKG_NAME" >&2
  exit 1
fi

rm -rf "$DOCS_DIR/_build"

for lang in en jp; do
  API_DIR="$DOCS_DIR/$lang/api"
  mkdir -p "$API_DIR"
  sphinx-apidoc --force --module-first -o "$API_DIR" "$SRC_DIR/$PKG_NAME"
done

for lang in en jp; do
  sphinx-build -n -W --keep-going -b html -D language="$([ "$lang" = jp ] && echo ja || echo en)" -c "$DOCS_DIR" "$DOCS_DIR/$lang" "$DOCS_DIR/_build/html/$lang"
done

# The English root is built from the same source as /en/.
sphinx-build -n -W --keep-going -b html -D language=en -c "$DOCS_DIR" "$DOCS_DIR/en" "$DOCS_DIR/_build/html"

touch "$DOCS_DIR/_build/html/.nojekyll"

if [ -f "$DOCS_DIR/_robots.txt" ]; then
  cp "$DOCS_DIR/_robots.txt" "$DOCS_DIR/_build/html/robots.txt"
fi

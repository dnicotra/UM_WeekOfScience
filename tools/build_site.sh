#!/usr/bin/env bash
# Build the GitHub Pages site: one WebAssembly page per notebook, sharing one copy of
# marimo's frontend assets, behind a hand-written landing page.
set -euo pipefail

MARIMO_VERSION="${MARIMO_VERSION:-0.25.0}"
OUT="${1:-site}"

# published name : notebook
NOTEBOOKS=(
  "double-slit:double_slit.py"
  "water-waves:water_waves.py"
)

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

# $OUT is wiped below, so keep it inside the repo.
case "$OUT" in
  "" | /* | *..*) echo "refusing to build into '$OUT'" >&2; exit 2 ;;
esac

build="$(mktemp -d)"
trap 'rm -rf "$build"' EXIT

rm -rf "$OUT"
mkdir -p "$OUT"

for entry in "${NOTEBOOKS[@]}"; do
  slug="${entry%%:*}"
  notebook="${entry#*:}"

  # Pinned, and deliberately a marimo-only environment: with numpy/plotly installed as well,
  # marimo rewrites the notebook's script header and pins their versions, and a pinned numpy
  # cannot be installed in the browser (Pyodide ships its own wasm32 build).
  echo "==> exporting $notebook as $slug.html"
  uvx "marimo@$MARIMO_VERSION" export html-wasm "$notebook" -o "$build/$slug" --mode run

  # Everything except the page itself is marimo's frontend, identical between the two
  # exports and named by content hash, so merging leaves one copy rather than one per
  # notebook. Hash names also mean a mismatched version would add files, never clobber.
  for item in "$build/$slug"/* "$build/$slug"/.[!.]*; do
    [ -e "$item" ] || continue
    [ "$(basename "$item")" = "index.html" ] && continue
    cp -R "$item" "$OUT/"
  done

  cp "$build/$slug/index.html" "$OUT/$slug.html"
done

cp pages/index.html "$OUT/index.html"
touch "$OUT/.nojekyll"   # keep Jekyll from eating asset paths

python3 tools/check_site.py "$OUT"
du -sh "$OUT"

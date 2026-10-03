#!/usr/bin/env bash
# Build the GitHub Pages site: one WebAssembly page per notebook and language, sharing one copy of
# marimo's frontend assets, behind a hand-written landing page.
set -euo pipefail

MARIMO_VERSION="${MARIMO_VERSION:-0.25.0}"
OUT="${1:-site}"

# published name : notebook : language
NOTEBOOKS=(
  "what-is-a-wave:what_is_a_wave.py:en"
  "water-waves:water_waves.py:en"
  "double-slit:double_slit.py:en"
  "measurement-logbook:measurement_logbook.py:en"
  "wat-is-een-golf:what_is_a_wave.py:nl"
  "watergolven:water_waves.py:nl"
  "dubbele-spleet:double_slit.py:nl"
  "meetlogboek:measurement_logbook.py:nl"
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
  IFS=: read -r slug notebook lang <<< "$entry"

  # Every notebook carries all its languages and shows the one on its LANG line, so another
  # language is the same notebook with that line rewritten. The copy is named after the slug
  # because the export takes the page title from the file name.
  if ! grep -q '^    LANG = "en"$' "$notebook"; then
    echo "error: $notebook must say LANG = \"en\" (left switched after a local preview?)" >&2
    exit 1
  fi
  source="$notebook"
  if [ "$lang" != "en" ]; then
    mkdir -p "$build/src"
    source="$build/src/${slug//-/_}.py"
    sed "s/^    LANG = \"en\"\$/    LANG = \"$lang\"/" "$notebook" > "$source"
    if ! grep -q "^    LANG = \"$lang\"\$" "$source"; then
      echo "error: $notebook has no 'LANG = \"en\"' line to switch to $lang" >&2
      exit 1
    fi
  fi

  # Pinned, and deliberately a marimo-only environment: with numpy/plotly installed as well,
  # marimo rewrites the notebook's script header and pins their versions, and a pinned numpy
  # cannot be installed in the browser (Pyodide ships its own wasm32 build).
  echo "==> exporting $notebook ($lang) as $slug.html"
  uvx "marimo@$MARIMO_VERSION" export html-wasm "$source" -o "$build/$slug" --mode run

  # Everything except the page itself is marimo's frontend, identical between the
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

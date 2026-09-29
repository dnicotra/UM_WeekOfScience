#!/usr/bin/env python3
"""Fail the build if a published page points at a file that is not in the site tree.

The pages are merged out of separate marimo exports, so a broken relative path is the
failure mode worth guarding against.
"""

import pathlib
import re
import sys

REFERENCE = re.compile(r"""(?:src|href)\s*=\s*["']([^"']+)["']""")
EXTERNAL = ("http://", "https://", "data:", "mailto:", "//", "#", "blob:")


def main(site: pathlib.Path) -> int:
    pages = sorted(site.glob("*.html"))
    if not pages:
        print(f"error: no pages in {site}", file=sys.stderr)
        return 1

    missing, checked = [], 0
    for page in pages:
        for ref in REFERENCE.findall(page.read_text(errors="replace")):
            if ref.startswith(EXTERNAL):
                continue
            clean = ref.split("?")[0].split("#")[0]
            if not clean:
                continue
            target = site / clean.lstrip("/")
            checked += 1
            if not target.exists():
                missing.append(f"{page.name} -> {ref}")

    for page in pages:
        print(f"  {page.name:24s} {page.stat().st_size / 1024:8.1f} KiB")
    print(f"  {len(pages)} pages, {checked} local references, {len(missing)} missing")

    for m in missing:
        print(f"error: missing reference: {m}", file=sys.stderr)
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "site")))

#!/usr/bin/env python3
"""Put learn_styles.css, learn_screens.html and learn_engine.js into index.html.

Each goes between its own markers so re-running replaces rather than duplicates — the app
stays one self-contained file while the source of the Learn mode stays editable on its own.
The CSS goes last in the stylesheet on purpose: an earlier rule of equal specificity wins on
source order, which has bitten this file before.
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
HTML = ROOT / "index.html"

PARTS = [
    ("css", "learn_styles.css", "/* LEARN:CSS", "*/", "</style>"),
    ("screens", "learn_screens.html", "<!-- LEARN:SCREENS", "-->", "  <!-- LEARNING PATH -->"),
    ("js", "learn_engine.js", "// LEARN:JS", "", "// ================= BOOT ================="),
]


def band(kind, body, o, c):
    return f"{o}:BEGIN {c}\n{body.rstrip()}\n{o}:END {c}\n"


def main():
    s = HTML.read_text()
    for kind, fname, o, c, anchor in PARTS:
        body = (ROOT / fname).read_text()
        block = band(kind, body, o, c)
        pat = re.compile(re.escape(f"{o}:BEGIN {c}") + r".*?" + re.escape(f"{o}:END {c}") + r"\n", re.S)
        if pat.search(s):
            s = pat.sub(lambda _: block, s, count=1)
            how = "replaced"
        else:
            if anchor not in s:
                print(f"anchor for {fname} not found: {anchor!r}", file=sys.stderr)
                sys.exit(1)
            s = s.replace(anchor, block + anchor, 1)
            how = "inserted"
        print(f"   {how} {fname} ({len(body)/1024:.1f} KB)")
    HTML.write_text(s)

    # every $('id') the engine touches must exist in the markup
    ids = set(re.findall(r'id="([^"]+)"', s))
    want = set(re.findall(r"\$\('([A-Za-z][\w-]*)'\)", (ROOT / "learn_engine.js").read_text()))
    missing = sorted(w for w in want if w not in ids)
    if missing:
        print("MISSING element ids: " + ", ".join(missing), file=sys.stderr)
        sys.exit(1)
    print(f"✓ index.html is {len(s)/1024/1024:.2f} MB · {len(want)} element ids checked")


if __name__ == "__main__":
    main()

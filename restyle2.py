#!/usr/bin/env python3
"""Second restyle pass: retire the hard-coded neon literals.

The first pass moved the tokens and the theme palettes, but ~110 rules and a few
canvas calls still named the old neons directly (rgba(60,224,255,…) and friends),
so those places stayed bright. Inside the stylesheet they become color-mix on the
token, which means a theme now reaches them too; in canvas code, where color-mix
is not available, they become the new literal.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
import re

PAGE = pathlib.Path(__file__).resolve().parent / "index.html"

# old literal -> (token, new literal)
PALETTE = {
    "60,224,255":  ("--cyan",   "122,182,214"),
    "255,79,216":  ("--mag",    "192,138,180"),
    "107,255,158": ("--lime",   "133,196,155"),
    "255,215,94":  ("--gold",   "212,174,118"),
    "255,93,108":  ("--red",    "212,132,142"),
    "155,107,255": ("--violet", "150,145,204"),
}

HEX = {
    # accents
    "#3ce0ff": "#7ab6d6", "#ff4fd8": "#c08ab4", "#6bff9e": "#85c49b",
    "#ffd75e": "#d4ae76", "#ff5d6c": "#d4848e", "#9b6bff": "#9691cc",
    "#ff9d4f": "#c79a68", "#c0392b": "#a8635c", "#ff2e63": "#c97b8a",
    "#ff2e2e": "#c9707a", "#ffa07a": "#d0a08f", "#ff6b6b": "#cf8585",
    # tinted text that never belonged to a token
    "#eaf4ff": "#e7ebf1", "#f4f9ff": "#e7ebf1", "#e9f3ff": "#e7ebf1",
    "#e4eefb": "#e7ebf1", "#dbe6f4": "#d3d9e2", "#c9d8ec": "#c3cbd6",
    "#cfe2f7": "#c3cbd6", "#8aa0bd": "#93a0b0",
    "#ffeaaa": "#e3cfa4", "#ddffe9": "#cfe6d8", "#dcffe9": "#cfe6d8",
    "#d8ffe6": "#cfe6d8", "#ffdde1": "#e8cdd1",
    # grounds
    "#05060f": "#0f1116", "#0a0e20": "#161a22", "#0b0f22": "#161a22",
    "#0d1220": "#161a22", "#04101a": "#10161c",
}


def main():
    s = PAGE.read_text(encoding="utf-8")
    style_end = s.index("</style>")
    css, rest = s[:style_end], s[style_end:]
    counts = {"mix": 0, "literal": 0, "hex": 0}

    def to_mix(m):
        counts["mix"] += 1
        token, _ = PALETTE[m.group(1)]
        alpha = float(m.group(2))
        return "color-mix(in srgb, var(%s) %d%%, transparent)" % (token, round(alpha * 100))

    def to_literal(m):
        counts["literal"] += 1
        _, rgb = PALETTE[m.group(1)]
        return "rgba(%s,%s)" % (rgb, m.group(2))

    pat = re.compile(r"rgba\((%s),\s*(\.\d+|\d?\.?\d+)\)" % "|".join(
        re.escape(k) for k in PALETTE))
    css = pat.sub(to_mix, css)
    rest = pat.sub(to_literal, rest)
    s = css + rest

    for old, new in HEX.items():
        n = s.count(old)
        if n:
            counts["hex"] += n
            s = s.replace(old, new)

    PAGE.write_text(s, encoding="utf-8")
    left = len(re.findall(pat, s))
    print(f"{counts['mix']} rules now mix the token, {counts['literal']} canvas colours "
          f"relettered, {counts['hex']} hex literals mapped, {left} left over")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Second OCR pass: the general rule, with domains protected from it.

The first pass only removed a stray period after a short function word, because that was
all I could justify without looking. Having looked at all 212 remaining cases, the general
rule holds: in these option texts a sentence never begins with a lowercase word, so a
period followed by one is always damage — "the put. item method", "prevent tag.
modification", "does not. have permission to pull. images".

With one exception that the general rule would wreck. "events. amazonaws. com" and
"application. example. com" are domain names the scrape split at every dot; there the
period is real and the SPACE is the damage. Domains are reassembled first, and the general
rule then leaves them alone.

Run once; index.html is the source of truth afterwards.
"""
import json, re, pathlib

PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
m = re.search(r'(<script id="data" type="application/json">)(.*?)(</script>)', s, re.S)
assert m, "question bank not found"
data = json.loads(m.group(2))

KEEP = {"etc", "eg", "ie", "vs", "no", "al", "inc", "ltd", "min", "max", "avg",
        "sec", "hr", "approx", "cf", "ex", "dr", "mr", "st", "am", "pm"}

TLD = r"(?:com|net|org|io|gov|edu|amazonaws|example|cloudfront|s3)"
DOMAIN = re.compile(r"\b([A-Za-z0-9][A-Za-z0-9-]*)\.\s+(?=[A-Za-z0-9-]+\.\s*" + TLD + r"\b|" + TLD + r"\b)")
# "s3- accelerate", "on- premises", "Site-to- Site" — a hyphen never takes a space after it
HYPHEN = re.compile(r"(?<=[A-Za-z0-9])-\s+(?=[A-Za-z0-9])")
PERIOD = re.compile(r"(?<![.\w])([A-Za-z]{2,})\.(\s+)(?=[a-z])")
DEBRIS = [
    (re.compile(r"\.\s*,\s*"), ". "),           # "account.,Grant"
    (re.compile(r":\s*\.\s*"), ": "),           # "minutes:.For"
    (re.compile(r"\b(Amazon|AWS)\.(?=[A-Z])"), r"\1 "),   # "AWS.WAF", "AWS.Management"
    (re.compile(r"\banew\b"), "a new"),          # "Create anew administrator account"
    (re.compile(r"\s+([:;])\s*[:;.]?\s*$"), ""),  # trailing " : ;"
]


def fix(t):
    prev = None
    while prev != t:                 # domains chain: a. b. com needs two passes
        prev = t
        t = DOMAIN.sub(r"\1.", t)
    t = HYPHEN.sub("-", t)
    t = PERIOD.sub(lambda mo: mo.group(0) if mo.group(1).lower() in KEEP
                   else mo.group(1) + mo.group(2), t)
    for pat, rep in DEBRIS:
        t = pat.sub(rep, t)
    return t


import difflib
def diffwords(a, b):
    aw, bw = a.split(), b.split()
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, aw, bw).get_opcodes():
        if tag != "equal":
            out.append(" ".join(aw[i1:i2]) + "  ->  " + " ".join(bw[j1:j2]))
    return out

nopt = nstem = 0
shown = 0
for qi, q in enumerate(data["questions"]):
    f = fix(q["q"])
    if f != q["q"]:
        nstem += 1
        q["q"] = f
    for p in q["o"]:
        f = fix(p[1])
        if f != p[1]:
            nopt += 1
            for d in diffwords(p[1], f):
                if shown < 24:
                    print("  q%-5d %s" % (qi, d)); shown += 1
            p[1] = f

print("\nrepaired %d option texts and %d stems" % (nopt, nstem))

import sys
if "--apply" not in sys.argv:
    print("(dry run — pass --apply to write)")
    sys.exit()

s = s[:m.start(2)] + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + s[m.end(2):]
PAGE.write_text(s, encoding="utf-8")
print("written · page %.2f MB" % (len(s) / 1e6))

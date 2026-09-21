#!/usr/bin/env python3
"""Translate the Learn-mode service cards, and scope the RTL rules properly.

Three loose ends after hebrew_codex.py and hebrew_glossary.py:

  1. #subjectdata carries the same service definitions a third time — 163
     `blueprint[].role` strings behind "Core services in this subject" and 84
     `tradeoffs[].benefit` strings in the trade-off table. Every one of the 86
     services named there is in the glossary and every wording is identical to
     it, so they take the same Hebrew.

  2. hebrew_codex.py put `direction:rtl` on `.svccard span` and on every
     `.exwhy .exitem span`. The first is right once (1) lands. The second is
     wrong for the "Decision rules for this sector" fallback, which is still
     English pulled from the course recap — RTL would throw its full stops to
     the left. That path gets an opt-out class.

  3. "Why the others don't" prints `<b>Service</b> — definition` inside an RTL
     span. Without its own isolation a term like `maxReceiveCount` loses its
     backticks to the far side of the line.

Run once; index.html is the source of truth afterwards.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from hebrew_glossary import G                     # noqa: E402  (the same 154 terms)

PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
HEB = re.compile(r"[֐-׿]")


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, "NOT FOUND (%d): %s" % (n, old[:90])
    s = s.replace(old, new, count)


# ------------------------------------------------- 1. the subject blueprints
m = re.search(r'(<script id="subjectdata" type="application/json">)(.*?)(</script>)', s, re.S)
assert m, "subjectdata blob not found"
data = json.loads(m.group(2).replace("<\\/", "</"))

roles = bens = 0
for sub_ in data["subjects"].values():
    for b in sub_["blueprint"]:
        assert b["svc"] in G, "no Hebrew for " + b["svc"]
        b["role"] = G[b["svc"]]
        roles += 1
    for t in sub_["tradeoffs"]:
        assert t["svc"] in G, "no Hebrew for " + t["svc"]
        t["benefit"] = G[t["svc"]]
        bens += 1

blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
s = s[:m.start()] + m.group(1) + blob + m.group(3) + s[m.end():]

chk = json.loads(re.search(r'<script id="subjectdata" type="application/json">(.*?)</script>',
                           s, re.S).group(1).replace("<\\/", "</"))
assert all(HEB.search(b["role"]) for v in chk["subjects"].values() for b in v["blueprint"])
assert all(HEB.search(t["benefit"]) for v in chk["subjects"].values() for t in v["tradeoffs"])

# ------------------------------------------ 2. the English fallback opts out
sub("""      bits.push('<div class="exwhy">'+rules.map(r=>'<div class="exitem"><span>'+mdInline(r)+'</span></div>').join('')+'</div>');""",
    """      bits.push('<div class="exwhy">'+rules.map(r=>'<div class="exitem ltr"><span>'+mdInline(r)+'</span></div>').join('')+'</div>');""")

# ------------------------------- 3. isolation for the inline term, and scoping
sub(""".concept b,.exwhy .exitem .k{direction:ltr;unicode-bidi:isolate}""",
    """.concept b,.exwhy .exitem .k,.exwhy .exitem b{direction:ltr;unicode-bidi:isolate}
/* the sector decision rules come out of the English course recap, so they keep
   their own direction — otherwise their full stops land on the wrong side */
.exwhy .exitem.ltr span{direction:ltr;text-align:left}
/* the trade-off table's benefit column now carries the same Hebrew as the cards */
.mdxtable td.heb{direction:rtl;unicode-bidi:isolate;text-align:right}""")

sub("""      d.tradeoffs.map(t=>'<tr><td><b>'+esc(t.svc)+'</b></td><td>'+mdInline(t.benefit)+'</td>'+""",
    """      d.tradeoffs.map(t=>'<tr><td><b>'+esc(t.svc)+'</b></td><td class="heb">'+mdInline(t.benefit)+'</td>'+""")

PAGE.write_text(s, encoding="utf-8")
print("blueprints translated · %d roles · %d benefits · page %.2f MB" % (roles, bens, len(s) / 1e6))

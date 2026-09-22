#!/usr/bin/env python3
"""Static audit of index.html — everything findable without a browser.

Reports, not fixes. Each finding carries a severity so the list can be triaged:
  HIGH   something is broken or will break for a user
  MED    wrong, misleading, or dead weight that will confuse the next reader
  LOW    cosmetic, stale copy, or a smell
"""
import collections
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
PAGE = HERE / "index.html"
s = PAGE.read_text(encoding="utf-8")

STYLE = s[s.index("<style>"):s.index("</style>")]
BODY_START = s.index("</style>")
HTML = s[BODY_START:s.index("<script>", BODY_START)]
JS = s[s.index("(function(){", BODY_START):]

found = []


def report(sev, area, what, evidence=""):
    found.append((sev, area, what, evidence))


def line_of(idx):
    return s[:idx].count("\n") + 1


# ------------------------------------------------------------------ ids
ids = re.findall(r'\sid="([A-Za-z0-9_-]+)"', s)
dupes = [i for i, c in collections.Counter(ids).items() if c > 1]
for d in dupes:
    report("HIGH", "markup", f'duplicate element id "{d}" — $() returns only the first',
           f"{collections.Counter(ids)[d]} occurrences")

# every $('x') must exist
touched = set(re.findall(r"\$\('([A-Za-z0-9_-]+)'\)", JS))
have = set(ids)
for t in sorted(touched - have):
    report("HIGH", "js", f"$('{t}') has no element — silent null")

# elements nothing ever touches (excluding ones used as anchors/containers in HTML)
never = sorted(have - touched)
skip_prefix = ("grid-bg", "app", "nav", "topbar", "data", "coursedata", "subjectdata",
               "explaindata", "rationaledata", "learndata", "studydata")
never = [n for n in never if not n.startswith(skip_prefix)]
cls_used = set(re.findall(r"getElementById\('([A-Za-z0-9_-]+)'\)", JS))
for n in never:
    if n in cls_used or ('"#' + n) in JS or ("#" + n) in STYLE:
        continue
    report("LOW", "markup", f'element id "{n}" is never read by any code')

# ------------------------------------------------------------ dead functions
defs = dict()
for m in re.finditer(r"^function ([A-Za-z0-9_]+)\(", JS, re.M):
    defs[m.group(1)] = m.start()
for name, at in sorted(defs.items()):
    uses = len(re.findall(r"(?<![A-Za-z0-9_.])" + re.escape(name) + r"\s*\(", JS))
    refs = len(re.findall(r"(?<![A-Za-z0-9_.])" + re.escape(name) + r"(?![A-Za-z0-9_(])", JS))
    if uses <= 1 and refs <= 1:
        report("MED", "js", f"function {name}() is defined but never called")

# ------------------------------------------------------- profile field hygiene
writes = collections.Counter(re.findall(r"P\.([A-Za-z0-9_]+)\s*=", JS))
reads = collections.Counter(re.findall(r"P\.([A-Za-z0-9_]+)(?!\s*=[^=])", JS))
for k in sorted(writes):
    if reads[k] <= writes[k] and reads[k] <= 1:
        report("LOW", "state", f"P.{k} is written but effectively never read")

# ------------------------------------------------------------- stale numbers
for pat, why in [
    (r"\b2502\b", "the old 2,502-question bank"),
    (r"\b2,502\b", "the old 2,502-question bank"),
    (r"Subject Course", "the Subject Course was replaced by Learn a Subject"),
    (r"Exam ×5|Exam x5", "the five-question drill was removed"),
    (r"5-question exam", "the five-question drill was removed"),
]:
    for m in re.finditer(pat, s):
        report("MED", "copy", f"stale reference: {why}",
               f"line {line_of(m.start())}: {s[max(0,m.start()-60):m.end()+40].strip()[:110]}")

# coin prices in prose, now that everything is free
for m in re.finditer(r"(costs? \d+ coins|\d+ coins? \(|Entry: \d+|Spend coins)", s):
    report("MED", "copy", "copy still talks about paying coins, but nothing costs coins",
           f"line {line_of(m.start())}: {s[max(0,m.start()-50):m.end()+50].strip()[:110]}")

# ------------------------------------------------------------- CSS hygiene
sel_counts = collections.Counter()
for m in re.finditer(r"(^|\})\s*([^{}@/]+?)\s*\{", STYLE, re.M):
    sel = " ".join(m.group(2).split())
    if sel and not sel.startswith(("@", "/*", "from", "to", "0%", "50%", "100%")):
        sel_counts[sel] += 1
for sel, c in sel_counts.items():
    if c > 1 and len(sel) < 60:
        report("LOW", "css", f'selector "{sel}" is declared {c} times — later wins silently')

# classes used in JS/HTML but never styled
css_classes = set(re.findall(r"\.([a-zA-Z][A-Za-z0-9_-]*)", STYLE))
used_classes = set()
for m in re.finditer(r'class="([^"]+)"', s):
    used_classes.update(m.group(1).split())
for m in re.finditer(r"className='([^']+)'", JS):
    used_classes.update(m.group(1).split())
for m in re.finditer(r"classList\.(?:add|toggle)\('([A-Za-z0-9_-]+)'", JS):
    used_classes.add(m.group(1))
unstyled = sorted(c for c in used_classes - css_classes if not c.startswith("hidden"))
for c in unstyled:
    report("LOW", "css", f'class "{c}" is applied but has no style rule')

# ------------------------------------------------------------ a11y basics
for m in re.finditer(r'<button([^>]*)>\s*([^<\s][^<]{0,3})\s*</button>', s):
    attrs, label = m.group(1), m.group(2).strip()
    if len(label) <= 2 and "aria-label" not in attrs and "title" not in attrs:
        report("MED", "a11y", "icon-only button with no aria-label or title",
               f"line {line_of(m.start())}: {m.group(0)[:70]}")

if 'lang="' not in s[:400]:
    report("MED", "a11y", "<html> has no lang attribute")
if not re.search(r'<meta name="description"', s):
    report("LOW", "seo", "no meta description")

# Hebrew inside an lang=en document without dir on every instance
heb_spans = len(re.findall(r'class="heb[^"]*"', s))
heb_dir = len(re.findall(r'class="heb[^"]*"[^>]*dir="rtl"', s))
if heb_spans and heb_dir < heb_spans:
    report("LOW", "a11y", f"{heb_spans - heb_dir} Hebrew spans rely on CSS direction only "
                          "(no dir attribute) — fine visually, weaker for screen readers")

# --------------------------------------------------------------- bank data
blob = re.search(r'<script id="data" type="application/json">(.*?)</script>', s, re.S).group(1)
bank = json.loads(blob.replace("<\\/", "</"))
qs = bank["questions"]
seen_stem = {}
for i, q in enumerate(qs):
    k = re.sub(r"\W+", "", q["q"].lower())[:400]
    if k in seen_stem:
        report("HIGH", "bank", f"question {i} duplicates question {seen_stem[k]}")
    seen_stem[k] = i
    if len(q["o"]) != len(set(t.strip().lower() for _, t in q["o"])):
        report("HIGH", "bank", f"question {i} repeats an option verbatim")
    for l, t in q["o"]:
        if len(t.strip()) < 8:
            report("MED", "bank", f"question {i} option {l} is suspiciously short: {t!r}")
        if re.match(r"^[A-F][\).\s]", t.strip()):
            report("MED", "bank", f"question {i} option {l} starts with a stray letter marker: {t[:40]!r}")
    # the stems say this three ways: "(Select TWO.)", "(Choose two.)", "(Select THREE.)".
    # Matching only "Select" reported three perfectly healthy questions as damaged.
    multi = re.search(r"\((?:Select|Choose)\s+(?:TWO|THREE|two|three)\.?\)", q["q"], re.I)
    if multi and len(q["a"]) < 2:
        report("HIGH", "bank", f"question {i} says Select/Choose TWO but has {len(q['a'])} answer(s)")
    if len(q["a"]) >= 2 and not multi:
        report("MED", "bank", f"question {i} needs {len(q['a'])} answers but the stem never says so")
    letters = [l for l, _ in q["o"]]
    if letters != list("ABCDEF")[:len(letters)]:
        report("HIGH", "bank", f"question {i} has gappy option letters {letters} — an option was lost")
    if "©" in q["q"] or "£" in q["q"]:
        report("MED", "bank", f"question {i} still has OCR glyph damage")

# study data
sblob = re.search(r'<script id="studydata" type="application/json">(.*?)</script>', s, re.S)
if sblob:
    study = json.loads(sblob.group(1).replace("<\\/", "</"))
    for ci, c in enumerate(study["chapters"]):
        for t in c["topics"]:
            if not t["blocks"]:
                report("HIGH", "study", f"{c['nm']} / {t['nm']} has no content")
            for b in t["blocks"]:
                if b["t"] == "p" and len(b.get("x", "")) < 40:
                    report("LOW", "study", f"{t['nm']}: a very short paragraph block")
                if b["t"] == "table":
                    if len(b["head"]) > 4:
                        report("LOW", "study", f"{t['nm']}: a {len(b['head'])}-column table will "
                                               "need horizontal scrolling on a phone")
        qids = [q["q"] for q in c["quiz"]]
        if len(qids) != len(set(qids)):
            report("MED", "study", f"{c['nm']} repeats a check question")

print(f"{len(found)} findings\n")
for sev in ("HIGH", "MED", "LOW"):
    rows = [f for f in found if f[0] == sev]
    if not rows:
        continue
    print(f"===== {sev} ({len(rows)}) =====")
    for _, area, what, ev in rows:
        print(f"  [{area}] {what}")
        if ev:
            print(f"        {ev}")
    print()

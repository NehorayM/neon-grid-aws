#!/usr/bin/env python3
"""Repair the questions OCR damaged, from the corrected CSV.

Twenty questions in the bank still carried damage: stray glyphs (the © that ended
up mid-sentence in three of them, "AwS", "SSUTLS", "rosolve", "Bey wants"),
options that had lost most of their text, options carrying a neighbour's text
behind a stray letter marker, a stem that had swallowed its own option A, and
four multi-answer questions whose "(Select TWO.)" had been dropped so the app
asked for two answers without ever saying so.

Nineteen of them are intact in aws_saa_questions_explained_FIXED_FINAL.csv and
take their text straight from it. The twentieth is not in that file and has its
one glyph fixed by hand.

**Text only.** The recorded answers are left exactly as they are: the CSV
disagrees with this bank on 27 answers and that was looked at and left alone
deliberately. Every repair asserts that the option letters still line up with
the answer already recorded, and refuses the swap otherwise.

BANKV is deliberately NOT bumped. It hashes question identity to invalidate
index-keyed progress, and nothing here adds, removes or reorders a question — so
bumping it would throw away everybody's history to fix a typo.

Run once; index.html is the source of truth afterwards.
"""
import csv
import difflib
import json
import pathlib
import re
import sys

csv.field_size_limit(10 ** 7)
HERE = pathlib.Path(__file__).resolve().parent
PAGE = HERE / "index.html"
SRC = pathlib.Path("/home/nehoray/Downloads/aws_saa_questions_explained_FIXED_FINAL.csv")

s = PAGE.read_text(encoding="utf-8")
m = re.search(r'(<script id="data" type="application/json">)(.*?)(</script>)', s, re.S)
bank = json.loads(m.group(2).replace("<\\/", "</"))
qs = bank["questions"]

rows = list(csv.DictReader(SRC.open(encoding="utf-8")))
norm = lambda t: re.sub(r"[^a-z0-9]+", "", (t or "").lower())
cn = [norm(r["question_text"]) for r in rows]

GLYPH = re.compile(r"[©£¢®¥§¶]|\bAwS\b|\bSSUTLS\b|\bUse-an\b|\brosolve\b|\bBey\b")
# The stems say this three different ways. Looking only for "Select" reported three healthy
# questions as damaged — audit_static.py had the same false positive and is fixed with it.
MULTI = re.compile(r"\((?:Select|Choose)\s+(?:TWO|THREE|two|three)\.?\)", re.I)

damaged = set()
for i, q in enumerate(qs):
    if GLYPH.search(q["q"]) or any(GLYPH.search(t) for _, t in q["o"]):
        damaged.add(i)
    if len(q["a"]) >= 2 and not MULTI.search(q["q"]):
        damaged.add(i)
    for l, t in q["o"]:
        if len(t.strip()) < 12 or re.match(r"^[A-F][\).\s]", t.strip()):
            damaged.add(i)

repaired, skipped, answers_kept_despite_csv, gained = [], [], [], []
for i in sorted(damaged):
    an = norm(qs[i]["q"])
    j = max(range(len(rows)), key=lambda j: difflib.SequenceMatcher(None, an, cn[j]).ratio())
    score = difflib.SequenceMatcher(None, an, cn[j]).ratio()
    r = rows[j]
    if score < 0.70:
        skipped.append((i, score))
        continue
    opts = [(l, r["option_" + l.lower()].strip())
            for l in "ABCDEF" if r["option_" + l.lower()].strip()]
    have = {l for l, _ in opts}
    # the recorded answer has to still exist in the repaired option set
    if not set(qs[i]["a"]) <= have:
        skipped.append((i, score))
        continue
    csv_ans = "".join(sorted(re.findall(r"[A-F]", r["correct_answer"].upper())))
    mine = "".join(sorted(qs[i]["a"]))
    if len(opts) != len(qs[i]["o"]):
        # the option set itself changes size — only safe when both sides agree on the
        # answer, otherwise a letter could come to mean something different
        if csv_ans != mine:
            skipped.append((i, score))
            continue
        gained.append((i, len(qs[i]["o"]), len(opts)))
    elif csv_ans != mine:
        answers_kept_despite_csv.append((i, mine, csv_ans))
    qs[i]["q"] = r["question_text"].strip()
    qs[i]["o"] = [[l, t] for l, t in opts]
    repaired.append((i, r["item_number"]))

# the one not in the CSV: a single OCR glyph in the stem
for i, q in enumerate(qs):
    if "AwS" in q["q"]:
        q["q"] = q["q"].replace("AwS", "AWS")
        repaired.append((i, "by hand"))

# Three questions had lost an option outright, so their letters ran A, B, C, E — the app
# rendered the gap and the reader saw a question with no D. One is intact in the CSV and was
# repaired above. The other two are not in that file and the missing text is simply gone, so
# the remaining options are relabelled to run in sequence and the recorded answer moves with
# them. That is a display repair, not an invention: no option's words change.
relabelled = []
for i, q in enumerate(qs):
    letters = [l for l, _ in q["o"]]
    want = list("ABCDEF")[:len(letters)]
    if letters == want:
        continue
    remap = dict(zip(letters, want))
    q["o"] = [[remap[l], txt] for l, txt in q["o"]]
    q["a"] = sorted(remap[l] for l in q["a"])
    relabelled.append((i, letters, want))
    if q.get("x"):
        for old_l, new_l in remap.items():
            if old_l != new_l:
                q["x"] = re.sub(r"\boption %s\b" % old_l, "option " + new_l, q["x"])

# nothing may be left damaged, and nothing may have moved
left = [i for i, q in enumerate(qs)
        if GLYPH.search(q["q"]) or any(GLYPH.search(t) for _, t in q["o"])]
assert not left, "still damaged: %s" % left
assert len(qs) == 1201, len(qs)
for q in qs:
    assert q["a"], "a question lost its answer"
    assert set(q["a"]) <= {l for l, _ in q["o"]}, "an answer points at no option"
    if len(q["a"]) >= 2:
        assert MULTI.search(q["q"]), "multi-answer with no Select/Choose: " + q["q"][:70]

blob = json.dumps(bank, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
s = s[:m.start()] + m.group(1) + blob + m.group(3) + s[m.end():]
chk = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',
                           s, re.S).group(1).replace("<\\/", "</"))
assert len(chk["questions"]) == 1201
PAGE.write_text(s, encoding="utf-8")

print("repaired %d questions" % len(repaired))
for i, item in repaired:
    print("   app#%-5d from %s" % (i, item))
if answers_kept_despite_csv:
    print("\nkept this bank's answer where the CSV disagreed (%d):" % len(answers_kept_despite_csv))
    for i, mine, theirs in answers_kept_despite_csv:
        print("   app#%-5d kept %-3s (CSV said %s)" % (i, mine, theirs))
if relabelled:
    print("\noptions relabelled to close a gap where one was lost for good (%d):" % len(relabelled))
    for i, was, now in relabelled:
        print("   app#%-5d %s -> %s" % (i, "".join(was), "".join(now)))
if gained:
    print("\noptions restored that had gone missing entirely (%d):" % len(gained))
    for i, was, now in gained:
        print("   app#%-5d %d options -> %d" % (i, was, now))
if skipped:
    print("\nnot repaired (%d):" % len(skipped))
    for i, sc in skipped:
        print("   app#%-5d best CSV match only %.2f" % (i, sc))
print("\npage %.2f MB" % (len(s) / 1e6))

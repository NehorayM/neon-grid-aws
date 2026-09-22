#!/usr/bin/env python3
"""Give every question a written explanation of each option, right and wrong.

The panel explained the correct answer by naming the services in it, and the
wrong ones only when they happened to name a service the right answer did not —
so most distractors got nothing at all.

aws_saa_questions_explained_FIXED_FINAL.csv carries a written explanation for all
1,210 questions, and they are the right shape: 1,179 of them name three or more
options by letter and say what is wrong with each. Median 416 characters.

**Only attached where the CSV agrees with this bank's answer.** The two disagree
on 27 questions, and an explanation arguing for C under a question this app marks
D is worse than no explanation at all. Those keep the sections they already had.

BANKV is not bumped: it hashes question identity (stem, options, answer, sector)
and none of that changes, so nobody's progress is invalidated for adding prose.

Run once; index.html is the source of truth afterwards.
"""
import csv
import difflib
import collections
import json
import pathlib
import re

csv.field_size_limit(10 ** 7)
HERE = pathlib.Path(__file__).resolve().parent
PAGE = HERE / "index.html"
SRC = pathlib.Path("/home/nehoray/Downloads/aws_saa_questions_explained_FIXED_FINAL.csv")

s = PAGE.read_text(encoding="utf-8")
m = re.search(r'(<script id="data" type="application/json">)(.*?)(</script>)', s, re.S)
bank = json.loads(m.group(2).replace("<\\/", "</"))
qs = bank["questions"]

rows = list(csv.DictReader(SRC.open(encoding="utf-8")))
words = lambda t: set(w for w in re.findall(r"[a-z0-9]+", (t or "").lower()) if len(w) > 3)
norm = lambda t: re.sub(r"[^a-z0-9]+", "", (t or "").lower())

cw = [words(r["question_text"]) for r in rows]
cn = [norm(r["question_text"]) for r in rows]
inv = collections.defaultdict(set)
for i, w in enumerate(cw):
    for tok in w:
        inv[tok].add(i)

attached = 0
skipped_answer = []
skipped_nomatch = 0
for qi, q in enumerate(qs):
    aw, an = words(q["q"]), norm(q["q"])
    score = collections.Counter()
    for tok in aw:
        for i in inv.get(tok, ()):
            score[i] += 1
    best, bestr = None, 0.0
    for i, _ in score.most_common(6):
        r = difflib.SequenceMatcher(None, an, cn[i]).ratio()
        if r > bestr:
            bestr, best = r, i
    if best is None or bestr < 0.85:
        skipped_nomatch += 1
        continue
    row = rows[best]
    csv_ans = "".join(sorted(re.findall(r"[A-F]", row["correct_answer"].upper())))
    if csv_ans != "".join(sorted(q["a"])):
        skipped_answer.append(qi)
        continue
    text = (row["explanation"] or "").strip()
    # the CSV prefixes some with bookkeeping about its own corrections; that is not for readers
    text = re.sub(r"^CORRECTED \(was [^)]*\)\.\s*", "", text)
    text = re.sub(r"^KEPT[^.]*\.\s*", "", text)
    if len(text) < 40:
        continue
    q["w"] = text
    attached += 1

assert attached > 1000, attached
blob = json.dumps(bank, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
s = s[:m.start()] + m.group(1) + blob + m.group(3) + s[m.end():]
chk = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',
                           s, re.S).group(1).replace("<\\/", "</"))
assert len(chk["questions"]) == 1201
assert sum(1 for q in chk["questions"] if q.get("w")) == attached
PAGE.write_text(s, encoding="utf-8")

print("attached %d explanations of %d questions" % (attached, len(qs)))
print("  skipped, the CSV disagrees on the answer: %d" % len(skipped_answer))
print("  skipped, no confident match:              %d" % skipped_nomatch)
print("page %.2f MB" % (len(s) / 1e6))

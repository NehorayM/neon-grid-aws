#!/usr/bin/env python3
""""1 questions", "1 answers", "1 chips": counts that never pluralise.

Every count in the app is interpolated straight into a sentence with a hard
plural after it. Most of the time the number is large enough that nobody notices,
but each of these reaches 1 in ordinary use — a paper with one question left to
export, a question needing one answer, a chest one away, a bet of one chip, a
pace of one question a day (which is what a date two years out produces).

A single `plural(n, word)` fixes the class rather than the instances.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
import re

PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")

# the helper
anchor = "const pctW=n=>{"
assert s.count(anchor) == 1
s = s.replace(anchor,
"""// "1 questions", "1 answers", "1 chips" — every count in the app was interpolated straight
// into a sentence with a hard plural after it, and each of these reaches 1 in normal use.
const plural=(n,word,many)=>n+' '+(Math.abs(Number(n))===1?word:(many||word+'s'));
""" + anchor, 1)

# Each entry: the exact expression as it appears, and the singular noun.
PAIRS = [
    ("'+n+' questions", "n", "question"),
    ("'+need+' answers", "need", "answer"),
    ("'+DAILY_TARGET+' questions", "DAILY_TARGET", "question"),
    ("'+def.reward+' coins", "def.reward", "coin"),
    ("'+pace.perDay+' questions", "pace.perDay", "question"),
    ("'+q.a.length+' answers", "q.a.length", "answer"),
    ("'+pool.length+' questions", "pool.length", "question"),
    ("'+r.n+' questions", "r.n", "question"),
    ("'+S.papers+' papers", "S.papers", "paper"),
    ("'+PAPER_COUNT+' papers", "PAPER_COUNT", "paper"),
    ("'+len+' questions", "len", "question"),
    ("'+list.length+' questions", "list.length", "question"),
    ("'+r.list.length+' questions", "r.list.length", "question"),
    ("'+WEEK_TARGET+' questions", "WEEK_TARGET", "question"),
    ("'+next+' coins", "next", "coin"),
    ("'+PICK_COST+' coins", "PICK_COST", "coin"),
    ("'+pace.remaining+' questions", "pace.remaining", "question"),
    ("'+v+' chips", "v", "chip"),
    ("'+s.youWon+' chips", "s.youWon", "chip"),
    ("'+r.granted+' chips", "r.granted", "chip"),
    ("'+r.got+' chips", "r.got", "chip"),
    ("'+d.modules.length+' parts", "d.modules.length", "part"),
]
n = 0
for old, expr, word in PAIRS:
    new = "'+plural(%s,'%s')+'" % (expr, word)
    c = s.count(old)
    if not c:
        continue
    s = s.replace(old, new)
    n += c

# the two that already handle it by hand are left alone; check none slipped through
bad = re.findall(r"\+' (questions|answers|coins|chips|papers|parts)\b", s)
PAGE.write_text(s, encoding="utf-8")
print("pluralised %d count strings; %d hard plurals left (checked by hand)" % (n, len(bad)))

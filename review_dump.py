#!/usr/bin/env python3
"""Print a slice of the cleaned questions for answer review."""
import json, sys, pathlib
qs = json.load(open(pathlib.Path(__file__).resolve().parent / "qsrc" / "questions_clean.json"))
a, b = int(sys.argv[1]), int(sys.argv[2])   # inclusive item numbers
for q in [x for x in qs if a <= x["item"] <= b]:
    print(f"#{q['item']} [csv:{','.join(q['csv']) or '-'}] {q['q']}")
    for l, t in q["o"]:
        print(f"  {l}) {t}")
    print()

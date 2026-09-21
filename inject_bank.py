#!/usr/bin/env python3
"""Put qsrc/bank.json into index.html as the #data blob.

The old bank's question indices are stored in the profile (seen, wrong,
bookmarks, spaced repetition), so the bank carries a version stamp and the
page clears anything index-keyed when that stamp changes.
"""
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
BANK = HERE / "qsrc" / "bank.json"
PAGE = HERE / "index.html"

RESET = """  // the question bank is index-keyed; a new bank invalidates anything that
  // stored an index, so those fields start over while progress is kept
  if(P.bank!==BANKV){
    P.bank=BANKV; P.seen={}; P.wrong=[]; P.marks=[]; P.sr={};
  }
"""


def main():
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    qs = bank["questions"]
    assert len(bank["sections"]) == len(bank["short"]) == 23, "23 sections expected"
    seen = set()
    for i, q in enumerate(qs):
        assert set(q) <= {"s", "q", "o", "a", "v", "x"}, f"q{i} has odd fields {set(q)}"
        assert {"s", "q", "o", "a", "v"} <= set(q), f"q{i} is missing a field"
        assert 0 <= q["s"] < 23, f"q{i} section out of range"
        assert q["a"] and all(a in {l for l, _ in q["o"]} for a in q["a"]), f"q{i} bad answer"
        assert len(q["o"]) >= 3, f"q{i} has too few options"
        k = re.sub(r"\W+", "", q["q"].lower())[:400]
        assert k not in seen, f"q{i} duplicates an earlier question"
        seen.add(k)

    blob = json.dumps(bank, ensure_ascii=False, separators=(",", ":"))
    # The stamp exists to detect "index 412 now points at a different question", so it
    # hashes what makes an index mean something — the stems, the options and the answers.
    # Adding an explanation to a question must not throw away anyone's progress.
    identity = json.dumps([[q["q"], q["o"], q["a"], q["s"]] for q in qs],
                          ensure_ascii=False, separators=(",", ":"))
    ver = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:10]

    s = PAGE.read_text(encoding="utf-8")
    pat = re.compile(r'(<script id="data" type="application/json">).*?(</script>)', re.S)
    assert pat.search(s), "#data block not found"
    # only "</" needs neutralising inside a <script> block; "\/" is a legal JSON escape
    s = pat.sub(lambda m: m.group(1) + blob.replace("</", "<\\/") + m.group(2), s, count=1)

    # the version constant
    if "const BANKV=" in s:
        s = re.sub(r"const BANKV='[^']*';", "const BANKV='%s';" % ver, s, count=1)
    else:
        anchor = "const QS=DATA.questions, SECTIONS=DATA.sections, SHORT=DATA.short||SECTIONS;"
        assert anchor in s, "bank loading line not found"
        s = s.replace(anchor, anchor + "\nconst BANKV='%s';" % ver, 1)

    # the reset, inside loadProfile right after the stored profile is merged in
    if "if(P.bank!==BANKV)" not in s:
        anchor = "    if(r) Object.assign(P,JSON.parse(r.value));\n  }catch(e){}\n"
        assert anchor in s, "loadProfile anchor not found"
        s = s.replace(anchor, anchor + RESET, 1)

    PAGE.write_text(s, encoding="utf-8")
    print(f"injected {len(qs)} questions (bank {ver}), page is {len(s) / 1e6:.2f} MB")


if __name__ == "__main__":
    sys.exit(main())

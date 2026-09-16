#!/usr/bin/env python3
"""Build the module-based learning data and inject it into index.html.

Authoring lives in learn_src/s??_*.py, one file per subject, each exporting SUBJECT.
Nothing reaches the app without passing every check in validate() — the content is
hand-authored, so the checks are what stop a typo becoming a question with no right
answer, a quiz about something the module never taught, or ten "A" answers in a row.
"""
import importlib.util, json, random, re, sys, pathlib, collections, zlib

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "learn_src"
HTML = ROOT / "index.html"
OUT = ROOT / "learn_data.json"

BLOCK_TYPES = {"h", "p", "list", "steps", "table", "flow", "split", "key", "trap", "note", "code", "dtree"}
VISUAL = {"table", "flow", "split", "dtree"}
CALLOUT = {"key", "trap"}
BAD_WORDS = re.compile(r"\b(TODO|TBD|lorem ipsum|FIXME|placeholder|xxx)\b", re.I)


class Bad(Exception):
    pass


def sections_from_html():
    txt = HTML.read_text()
    m = re.search(r'<script id="data" type="application/json">(.*?)</script>', txt, re.S)
    d = json.loads(m.group(1))
    return d["sections"], d.get("short") or d["sections"], d["questions"]


def text_of(block):
    """Every human-readable string in a block, flattened — used for coverage checks."""
    t = block.get("t")
    out = []
    if t in ("h", "p", "key", "trap", "note", "code"):
        out.append(block.get("x", ""))
    elif t in ("list", "steps", "flow"):
        out.extend(block.get("x", []))
    elif t == "table":
        out.extend(block.get("head", []))
        for r in block.get("rows", []):
            out.extend(r)
    elif t == "split":
        for c in block.get("cols", []):
            out.append(c.get("nm", ""))
            out.extend(c.get("items", []))
    elif t == "dtree":
        for r in block.get("x", []):
            out.extend(r)
    out.append(block.get("cap", "") or "")
    return " ".join(out)


# Capitalised words are the signal for "a named AWS thing". The first word of a sentence is
# capitalised for grammar, not meaning, so it is dropped before looking.
STOP = {"Use", "Using", "With", "For", "And", "But", "Not", "Only", "Both", "All", "Each",
        "Its", "Their", "There", "These", "Those", "AWS", "Amazon", "Every", "Any", "Some",
        "Most", "More", "Less", "Least", "Team", "Company", "Customer", "Solutions",
        "Architect", "After", "Before", "During", "Because", "You", "Your", "The", "This",
        "That", "They", "What", "Which", "When", "Why", "How", "Yes", "Two", "One", "New"}


def terms(s, strip_lead=True):
    # in a question, a leading capital is grammar; in the module body it may be the only
    # mention of a real term, so the body is read without stripping anything
    s = s or ""
    if strip_lead:
        s = re.sub(r"(?:^|(?<=[.!?;:])\s+|\n\s*)([A-Za-z][\w'-]*)", " ", s)
    out = set()
    for w in re.findall(r"\b[A-Za-z][A-Za-z0-9]+\b", s):
        if not w[0].isupper() or w in STOP:
            continue
        # S3 and EC2 are as much a name as Lambda is; "Its" is not
        if w.isupper() or any(c.isdigit() for c in w) or len(w) > 3:
            out.add(w)
    return out


def stems(ws):
    """Compare terms without caring about plurals: Dedicated Hosts teaches Dedicated Host."""
    return {w[:-1].lower() if len(w) > 3 and w.endswith("s") else w.lower() for w in ws}


def norm_question(q, pos=None):
    """Normalised option/answer shape: o -> [{t, w}], a -> [int].

    Options are shuffled here with a seed derived from the question text: stable across
    rebuilds, but it stops hand-authored answers from clustering at position A. The app
    shuffles again per attempt; this is the belt to that pair of braces. A question whose
    options read as a sequence can opt out with fix=True.
    """
    opts = q["o"]
    notes = q.get("w") or []
    o = []
    for i, t in enumerate(opts):
        if isinstance(t, dict):
            o.append({"t": t["t"], "w": t.get("w", "")})
        else:
            o.append({"t": t, "w": notes[i] if i < len(notes) else ""})
    n = len(o)
    rng = random.Random(zlib.crc32(q["q"].encode()))
    if q.get("fix"):
        order = list(range(n))
    elif len(q["a"]) == 1:
        # the answer's position cycles through the options across the subject, so no
        # position is ever the likely one; the distractors around it are still seeded from
        # the question text, and the app shuffles again on every attempt
        rest = [i for i in range(n) if i != q["a"][0]]
        rng.shuffle(rest)
        at = (pos if pos is not None else rng.randrange(n)) % n
        order = rest[:at] + [q["a"][0]] + rest[at:]
    else:
        order = list(range(n))
        rng.shuffle(order)
    o = [o[i] for i in order]
    ans = sorted(order.index(a) for a in q["a"])
    out = {"q": q["q"], "o": o, "a": ans, "x": q["x"]}
    if q.get("m"):
        out["m"] = q["m"]
    return out


def check_md(where, s, errs):
    if s is None:
        return
    if s.count("**") % 2:
        errs.append(f"{where}: unbalanced ** in {s[:60]!r}")
    if s.count("`") % 2:
        errs.append(f"{where}: unbalanced backtick in {s[:60]!r}")
    if BAD_WORDS.search(s):
        errs.append(f"{where}: placeholder text in {s[:60]!r}")
    if s.strip() == "":
        errs.append(f"{where}: empty string")


def validate_question(where, q, errs, *, need_w, min_x):
    check_md(where, q["q"], errs)
    if not q["q"].rstrip().endswith("?"):
        errs.append(f"{where}: question does not end with '?' — {q['q'][:60]!r}")
    if not 3 <= len(q["o"]) <= 5:
        errs.append(f"{where}: {len(q['o'])} options, want 3-5")
    seen = set()
    for i, o in enumerate(q["o"]):
        check_md(f"{where} opt{i}", o["t"], errs)
        key = re.sub(r"\W+", "", o["t"].lower())
        if key in seen:
            errs.append(f"{where}: duplicate option text {o['t'][:40]!r}")
        seen.add(key)
        if need_w:
            if len(o["w"].strip()) < 15:
                errs.append(f"{where} opt{i}: needs a per-option note (why it wins/fails)")
            check_md(f"{where} opt{i}.w", o["w"], errs)
    if not q["a"]:
        errs.append(f"{where}: no correct answer marked")
    if len(q["a"]) > 2:
        errs.append(f"{where}: more than two correct answers")
    if len(set(q["a"])) != len(q["a"]):
        errs.append(f"{where}: duplicate answer index")
    for a in q["a"]:
        if not 0 <= a < len(q["o"]):
            errs.append(f"{where}: answer index {a} out of range")
    if len(q["a"]) == len(q["o"]):
        errs.append(f"{where}: every option marked correct")
    if len(q["x"].strip()) < min_x:
        errs.append(f"{where}: explanation is {len(q['x'].strip())} chars, want >= {min_x}")
    check_md(f"{where}.x", q["x"], errs)
    if len(q["a"]) > 1 and not re.search(r"\(choose two\)|\(select two\)|two\b", q["q"], re.I):
        errs.append(f"{where}: two correct answers but the stem does not say 'choose two'")


def validate(s, sections, shorts, errs):
    sec = s["sec"]
    pre = f"sec{sec}"
    if not 0 <= sec < len(sections):
        errs.append(f"{pre}: section index out of range")
        return
    mods = s["modules"]
    if not 3 <= len(mods) <= 8:
        errs.append(f"{pre}: {len(mods)} modules, want 3-8")
    ids = [m["id"] for m in mods]
    if len(set(ids)) != len(ids):
        errs.append(f"{pre}: duplicate module id")
    qtexts = collections.Counter()
    answer_pos = collections.Counter()
    total_checks = 0

    for m in mods:
        mp = f"{pre}/{m['id']}"
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", m["id"]):
            errs.append(f"{mp}: module id must be kebab-case")
        check_md(mp + ".nm", m["nm"], errs)
        check_md(mp + ".goal", m["goal"], errs)
        if len(m["goal"].strip()) < 25:
            errs.append(f"{mp}: goal is too short to mean anything")
        blocks = m["blocks"]
        if len(blocks) < 5:
            errs.append(f"{mp}: {len(blocks)} blocks, want >= 5")
        kinds = collections.Counter()
        for i, b in enumerate(blocks):
            if b["t"] not in BLOCK_TYPES:
                errs.append(f"{mp} block{i}: unknown type {b['t']!r}")
                continue
            kinds[b["t"]] += 1
            check_md(f"{mp} block{i}", text_of(b), errs)
            if b["t"] == "table":
                w = len(b["head"])
                if w < 2:
                    errs.append(f"{mp} block{i}: table needs >= 2 columns")
                for r in b["rows"]:
                    if len(r) != w:
                        errs.append(f"{mp} block{i}: row has {len(r)} cells, header has {w}")
                if len(b["rows"]) < 2:
                    errs.append(f"{mp} block{i}: table needs >= 2 rows")
            if b["t"] == "split":
                if len(b["cols"]) < 2:
                    errs.append(f"{mp} block{i}: split needs >= 2 columns")
                for c in b["cols"]:
                    if not c.get("items"):
                        errs.append(f"{mp} block{i}: split column {c.get('nm')!r} is empty")
            if b["t"] == "flow" and len(b["x"]) < 2:
                errs.append(f"{mp} block{i}: flow needs >= 2 nodes")
            if b["t"] == "dtree":
                for r in b["x"]:
                    if len(r) != 2:
                        errs.append(f"{mp} block{i}: dtree rows are [condition, verdict]")
        if not (set(kinds) & VISUAL):
            errs.append(f"{mp}: no table/flow/split/dtree — every module needs something visual")
        if not (set(kinds) & CALLOUT):
            errs.append(f"{mp}: no key/trap callout")
        body = " ".join(text_of(b) for b in blocks)
        if len(body) < 900:
            errs.append(f"{mp}: body is {len(body)} chars, want >= 900 — too thin to learn from")

        checks = m["checks"]
        if not 3 <= len(checks) <= 5:
            errs.append(f"{mp}: {len(checks)} checks, want 3-5")
        body_terms = terms(body, strip_lead=False)
        for j, q in enumerate(checks):
            total_checks += 1
            where = f"{mp} check{j}"
            validate_question(where, q, errs, need_w=False, min_x=40)
            qtexts[re.sub(r"\W+", "", q["q"].lower())] += 1
            for a in q["a"]:
                answer_pos[a] += 1
            asked = terms(q["q"] + " " + " ".join(q["o"][a]["t"] for a in q["a"]))
            # one capitalised word is not enough signal to judge — a place name or a
            # product word would fail a check that is meant to catch untaught services
            if len(asked) > 1:
                have, want = stems(body_terms), stems(asked)
                hit = len(want & have) / len(want)
                if hit < 0.5:
                    missing = sorted(w for w in asked if stems({w}) - have)
                    errs.append(f"{where}: only {hit:.0%} of its key terms appear in the module "
                                f"— asking about untaught material: {missing}")

    recap = s["recap"]
    if len(recap) < 6:
        errs.append(f"{pre}: recap has {len(recap)} blocks, want >= 6")
    if sum(1 for b in recap if b["t"] == "table") < 2:
        errs.append(f"{pre}: recap needs >= 2 tables")
    for i, b in enumerate(recap):
        if b["t"] not in BLOCK_TYPES:
            errs.append(f"{pre} recap block{i}: unknown type {b['t']!r}")
        else:
            check_md(f"{pre} recap block{i}", text_of(b), errs)
            if b["t"] == "table":
                w = len(b["head"])
                for r in b["rows"]:
                    if len(r) != w:
                        errs.append(f"{pre} recap block{i}: row has {len(r)} cells, header has {w}")

    final = s["final"]
    if len(final) != 10:
        errs.append(f"{pre}: final has {len(final)} questions, want exactly 10")
    covered = set()
    for j, q in enumerate(final):
        where = f"{pre} final{j}"
        validate_question(where, q, errs, need_w=True, min_x=80)
        qtexts[re.sub(r"\W+", "", q["q"].lower())] += 1
        for a in q["a"]:
            answer_pos[a] += 1
        mid = q.get("m")
        if mid not in ids:
            errs.append(f"{where}: m={mid!r} is not a module of this subject")
        else:
            covered.add(mid)
    if len(ids) <= 10:
        missed = [i for i in ids if i not in covered]
        if missed:
            errs.append(f"{pre}: final exam never touches module(s) {missed}")

    dupes = [q for q, n in qtexts.items() if n > 1]
    if dupes:
        errs.append(f"{pre}: {len(dupes)} question(s) appear more than once in the subject")

    tot = sum(answer_pos.values())
    if tot:
        worst, n = answer_pos.most_common(1)[0]
        if n / tot > 0.45:
            errs.append(f"{pre}: option {worst} is the answer {n}/{tot} times ({n/tot:.0%}) "
                        f"— answers are not spread across positions")
    mins = sum(m.get("min", 8) for m in mods)
    return {"modules": len(mods), "checks": total_checks, "final": len(final), "min": mins}


def normalize(s):
    """One pass over a subject, numbering questions so answer positions cycle evenly."""
    n = [0]

    def q(raw):
        out = norm_question(raw, n[0])
        n[0] += 1
        return out

    return {
        "sec": s["sec"], "nm": s["nm"], "tag": s.get("tag", ""),
        "modules": [{"id": m["id"], "nm": m["nm"], "goal": m["goal"], "min": m.get("min", 8),
                     "blocks": m["blocks"], "checks": [q(x) for x in m["checks"]]}
                    for m in s["modules"]],
        "recap": s["recap"],
        "final": [q(x) for x in s["final"]],
    }


def load():
    subs = []
    for p in sorted(SRC.glob("s*.py")):
        spec = importlib.util.spec_from_file_location(p.stem, p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "SUBJECT"):
            raise Bad(f"{p.name} has no SUBJECT")
        subs.append((p.name, mod.SUBJECT))
    return subs


def main():
    sections, shorts, questions = sections_from_html()
    subs = load()
    errs, stats, seen = [], {}, set()
    out = {}
    for name, s in subs:
        if s["sec"] in seen:
            errs.append(f"{name}: section {s['sec']} authored twice")
        seen.add(s["sec"])
        rec = normalize(s)
        st = validate(rec, sections, shorts, errs)
        if st:
            stats[s["sec"]] = st
        out[str(s["sec"])] = rec

    if errs:
        print(f"\n{len(errs)} problem(s) — nothing was written:\n", file=sys.stderr)
        for e in errs:
            print("  ✗ " + e, file=sys.stderr)
        sys.exit(1)

    payload = {"v": 1, "subjects": out}
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(blob)

    html = HTML.read_text()
    tag = '<script id="learndata" type="application/json">'
    if tag in html:
        html = re.sub(r'<script id="learndata" type="application/json">.*?</script>',
                      lambda _: tag + blob + "</script>", html, flags=re.S)
    else:
        anchor = '<script id="data" type="application/json">'
        if anchor not in html:
            raise Bad("could not find the question data block to anchor against")
        html = html.replace(anchor, tag + blob + "</script>\n" + anchor, 1)
    HTML.write_text(html)

    done = sum(st["modules"] for st in stats.values())
    print(f"✓ {len(out)}/{len(sections)} subjects · {done} modules · "
          f"{sum(st['checks'] for st in stats.values())} check questions · "
          f"{sum(st['final'] for st in stats.values())} exam questions")
    for sec in sorted(stats):
        st = stats[sec]
        print(f"   {sec:>2}  {shorts[sec][:34]:<34} {st['modules']} modules · "
              f"{st['checks']:>2} checks · ~{st['min']} min")
    todo = [i for i in range(len(sections)) if str(i) not in out]
    if todo:
        print(f"   not yet authored: {', '.join(shorts[i] for i in todo)}")
    print(f"   {len(blob)/1024:.0f} KB injected into index.html")


if __name__ == "__main__":
    main()

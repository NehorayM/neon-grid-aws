"""Build the structured per-subject content the Subject Course phases render.

Everything here is extracted from AWS-SAA-C03-Combined.md and carries a `src` field, so
every cell on screen can be traced back to a sentence in the study guide. Nothing is
invented: where the guide says nothing about a subject's limits or trade-offs, the entry is
simply absent and the app says so rather than padding the screen with plausible-sounding
AWS facts.

Output: subject_content.json  (+ injected into index.html as <script id="subjectdata">)
Run:    python3 build_subject_content.py
"""
import json
import os
import re

MD = "AWS-SAA-C03-Combined.md"
HTML = "index.html"
OUT = "subject_content.json"

md = open(MD, encoding="utf-8").read()

TOPIC = re.compile(r'^## (\d+)\. (.+)$', re.M)
SUB = re.compile(r'^### (.+)$', re.M)


def sentences(text):
    text = re.sub(r'\|[^\n]*\|', ' ', text)          # tables are handled separately
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z**])', text)
    return [re.sub(r'\s+', ' ', p).strip() for p in parts if len(p.strip()) > 40]


def clean(s, cap=260):
    s = re.sub(r'\s+', ' ', s).strip().strip('-–— ')
    if len(s) > cap:
        cut = s[:cap].rsplit(' ', 1)[0]
        s = cut + '…'
    return s


# ---------------------------------------------------------------- shared reference data
def parse_tables(text):
    """Every markdown table in a block, as {head:[...], rows:[[...]]}."""
    out, cur = [], []
    for line in text.split('\n'):
        if line.strip().startswith('|'):
            cur.append(line)
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    tables = []
    for block in out:
        rows = [[c.strip() for c in l.strip().strip('|').split('|')] for l in block
                if not re.match(r'^\s*\|[\s:|-]+\|?\s*$', l)]
        if len(rows) >= 2:
            tables.append({"head": rows[0], "rows": rows[1:]})
    return tables


glossary_block = md.split("## Master Glossary")[-1] if "## Master Glossary" in md else ""
GLOSSARY = []
for t in parse_tables(glossary_block):
    for r in t["rows"]:
        if len(r) >= 2 and r[0] and not r[0].lower().startswith("term"):
            GLOSSARY.append((r[0], r[1]))

SCENARIOS = []
m = re.search(r'## Master Scenario Table.*?(?=\n## Exam-Day Strategy|\n## Master Glossary)', md, re.S)
if m:
    for t in parse_tables(m.group(0)):
        for r in t["rows"]:
            if len(r) >= 2 and r[0] and not r[0].lower().startswith(("if the", "keyword")):
                SCENARIOS.append((r[0], r[1]))

STOP = {"aws", "region", "regions", "data", "service", "services", "the", "and"}


GENERIC = {"database", "databases", "service", "services", "policy", "policies", "storage",
           "instance", "instances", "gateway", "access", "mode", "modes", "class", "classes"}


def count_term(term, hay_low):
    """Count real mentions, tolerating plurals, and falling back to a multi-word term's
    distinctive head noun so 'Read Replica' still matches 'up to 5 replicas'."""
    t = term.lower().strip()
    if len(t) < 3 or t in STOP:
        return 0
    parts = [p.strip() for p in re.split(r'\s*[/,]\s*| or ', t) if len(p.strip()) >= 3]
    n = sum(len(re.findall(r'(?<![a-z0-9])' + re.escape(p) + r's?(?![a-z0-9])', hay_low))
            for p in parts)
    if n:
        return n
    for p in parts:
        words = p.split()
        if len(words) > 1:
            head = words[-1]
            if len(head) >= 6 and head not in GENERIC:
                n += len(re.findall(r'(?<![a-z0-9])' + re.escape(head) + r's?(?![a-z0-9])', hay_low))
    return n


# ---------------------------------------------------------------- extractors
LIMIT_RE = re.compile(
    r'\b(up to|maximum of|max\b|limit of|limited to|cannot exceed|at most|no more than|'
    r'minimum|required above|capped at|per second|per shard|hard limit)\b', re.I)
COST_RE = re.compile(
    r'\b(billed|bills|pay[- ]per|per GB|per-GB|per hour|hourly|free|no charge|costs?|'
    r'pricing|priced|cheaper|more expensive|\$\d)\b', re.I)
NEVER_RE = re.compile(
    r'\b(wrong answer|never the right|is not|isn\'t|cannot|can\'t|does not|doesn\'t|'
    r'the trap|reliable wrong|rules out|not a substitute|avoid)\b', re.I)

INTEGRATION_AREAS = [
    ("IAM & access", r'\b(IAM|role|trust policy|permission|SCP|least privilege|identity)\b'),
    ("Encryption & KMS", r'\b(KMS|encrypt|encryption|SSE-|TLS|at rest|in transit)\b'),
    ("Private networking", r'\b(VPC endpoint|PrivateLink|gateway endpoint|interface endpoint|private subnet|NAT)\b'),
    ("Observability & audit", r'\b(CloudWatch|CloudTrail|Config|X-Ray|metric|log|alarm|trace)\b'),
]


def blueprint_for(text, limit=8):
    low = text.lower()
    scored = [(count_term(t, low), t, d) for t, d in GLOSSARY]
    strong = [s for s in scored if s[0] >= 2]
    if len(strong) < 3:                       # short subjects mention things once, not twice
        strong = [s for s in scored if s[0] >= 1]
    scored = sorted(strong, key=lambda x: (-x[0], -len(x[1])))
    seen, out = set(), []
    for n, t, d in scored:
        k = t.lower()
        if any(k in s or s in k for s in seen):
            continue
        seen.add(k)
        out.append({"svc": t, "role": clean(d, 150), "hits": n, "src": "guide-glossary"})
        if len(out) >= limit:
            break
    return out


def decision_for(text, limit=10):
    low = text.lower()
    rows = []
    seen = set()
    for cue, ans in SCENARIOS:
        if ans in seen:
            continue
        terms = [t for t, _ in GLOSSARY if count_term(t, ans.lower())]
        weight = max([count_term(t, low) for t in terms] or [0])
        if weight >= 3:
            seen.add(ans)
            rows.append({"if": clean(cue, 120), "then": clean(ans, 140), "w": weight,
                         "src": "guide-scenario-table"})
    if len(rows) < 3:                          # thin subject: accept a weaker but real match
        for cue, ans in SCENARIOS:
            if ans in seen:
                continue
            terms = [t for t, _ in GLOSSARY if count_term(t, ans.lower())]
            weight = max([count_term(t, low) for t in terms] or [0])
            if weight == 2:
                seen.add(ans)
                rows.append({"if": clean(cue, 120), "then": clean(ans, 140), "w": weight,
                             "src": "guide-scenario-table"})
    rows.sort(key=lambda r: -r["w"])
    return rows[:limit]


def limits_for(text, limit=8):
    out, seen = [], set()
    for s in sentences(text):
        if LIMIT_RE.search(s) and re.search(r'\d', s):
            c = clean(s, 240)
            key = c[:60].lower()
            if key in seen:
                continue
            seen.add(key)
            out.append({"note": c, "src": "guide-prose"})
            if len(out) >= limit:
                break
    return out


def traps_for(subs, limit=10):
    """Common-mistakes lists and failure-pattern call-outs, split into individual traps."""
    out = []
    blob = "\n".join(v for k, v in subs.items())
    for para in re.findall(r'Common mistakes[^:]*:(.+?)(?:\n\n|$)', blob, re.S):
        for piece in re.split(r';\s*(?:and\s+)?', para):
            c = clean(piece, 210)
            if len(c) > 30:
                out.append({"trap": c[0].upper() + c[1:], "kind": "common mistake",
                            "src": "guide-common-mistakes"})
    for para in re.findall(r'\*\*Recognizing the failure pattern\.?\*\*(.+?)(?:\n\n|$)', blob, re.S):
        c = clean(para, 300)
        if c:
            out.append({"trap": c, "kind": "failure pattern", "src": "guide-failure-pattern"})
    return out[:limit]


def mistake_clauses(text):
    """The guide's common-mistakes lists, split into individual 'do not do this' clauses —
    the honest source for a 'never choose when' column."""
    out = []
    for para in re.findall(r'Common mistakes[^:]*:(.+?)(?:\n\n|$)', text, re.S):
        for piece in re.split(r';\s*(?:and\s+)?', para):
            c = clean(piece, 170)
            if 25 < len(c) < 175:
                out.append(c[0].lower() + c[1:])
    return out


def tidy_cell(s, cap=150, keep=None):
    """Trim to the clause that carries the evidence, not blindly to the first sentence —
    the limit or the price is often in the second half of the sentence."""
    s = re.sub(r'^\s*(Common mistakes[^:]*:|The recurring[^:]*:)', '', s).strip()
    parts = re.split(r'(?<=[.!?])\s+|\s+—\s+|;\s+', s)
    if keep:
        hit = next((p for p in parts if keep.search(p)), None)
        if hit:
            return clean(hit, cap)
    return clean(parts[0] if parts else s, cap)


def tradeoffs_for(text, subs, limit=8):
    """Five-column trade-off rows. Every cell is a clause the guide actually wrote about that
    service, matched to the right column: limits from limit statements, cost from pricing
    statements, and 'never choose' from the common-mistakes list. A cell with no clean
    source stays empty rather than borrowing a sentence that means something else."""
    low = text.lower()
    # limits and costs must not come from the mistakes paragraph - that is a different claim
    body = re.sub(r'Common mistakes[^:]*:.+?(?:\n\n|$)', ' ', text, flags=re.S)
    sents = [x for x in sentences(body) if len(x) < 400]
    nevers = mistake_clauses(text)
    rows = []
    for svc in blueprint_for(text, limit):
        name = svc["svc"]
        about = [s for s in sents if count_term(name, s.lower())]
        limit_s = next((s for s in about if LIMIT_RE.search(s) and re.search(r'\d', s)), "")
        cost_s = next((s for s in about if COST_RE.search(s)), "")
        never_s = next((n for n in nevers if count_term(name, n.lower())), "")
        limit_c = tidy_cell(limit_s, 150, re.compile(LIMIT_RE.pattern + r'|\d', re.I))
        cost_c = tidy_cell(cost_s, 150, COST_RE)
        never_c = tidy_cell(never_s, 165)
        filled = sum(1 for x in (limit_c, cost_c, never_c) if x)
        rows.append({
            "svc": name,
            "benefit": clean(svc["role"], 140),
            "limit": limit_c,
            "cost": cost_c,
            "never": never_c,
            "filled": filled,
            "src": "guide-prose",
        })
    rows.sort(key=lambda r: -r["filled"])
    return [r for r in rows if r["filled"] >= 1][:limit]


def integrations_for(text, limit=2):
    sents = sentences(text)
    out = []
    for area, pat in INTEGRATION_AREAS:
        rx = re.compile(pat, re.I)
        hits = [clean(s, 230) for s in sents if rx.search(s)][:limit]
        if hits:
            out.append({"area": area, "notes": hits, "src": "guide-prose"})
    return out


def guide_tables_for(block, limit=3):
    """The guide's own comparison tables, kept verbatim — already authored comparisons."""
    out = []
    for t in parse_tables(block):
        if 3 <= len(t["head"]) <= 5 and len(t["rows"]) >= 2:
            out.append({"head": t["head"], "rows": t["rows"][:8], "src": "guide-table"})
        if len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------- build
topics = list(TOPIC.finditer(md))
subjects = {}
for i, mt in enumerate(topics):
    num = int(mt.group(1))
    if num > 23:
        continue
    name = mt.group(2).strip()
    start, end = mt.end(), (topics[i + 1].start() if i + 1 < len(topics) else len(md))
    block = md[start:end]

    ms = list(SUB.finditer(block))
    subs = {}
    for j, s in enumerate(ms):
        a, b = s.end(), (ms[j + 1].start() if j + 1 < len(ms) else len(block))
        subs[s.group(1).strip()] = block[a:b].strip()

    overview = subs.get("Topic Overview & Architectural Deep-Dive", "")
    deep_key = next((k for k in subs if k.startswith("עומק נוסף")), None)
    deep = subs.get(deep_key, "") if deep_key else ""
    text = overview + "\n" + deep

    entry = {
        "i": num - 1,
        "nm": name,
        "blueprint": blueprint_for(text),
        "decision": decision_for(text),
        "tradeoffs": tradeoffs_for(text, subs),
        "guideTables": guide_tables_for(block),
        "traps": traps_for(subs),
        "limits": limits_for(text),
        "integrations": integrations_for(text),
    }
    entry["coverage"] = {k: len(entry[k]) for k in
                         ("blueprint", "decision", "tradeoffs", "guideTables", "traps", "limits", "integrations")}
    subjects[str(num - 1)] = entry

data = {"subjects": subjects, "builtFrom": MD}
json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# inject
html = open(HTML, encoding="utf-8").read()
blob = '<script id="subjectdata" type="application/json">' + open(OUT, encoding="utf-8").read() + '</script>'
if '<script id="subjectdata"' in html:
    html = re.sub(r'<script id="subjectdata" type="application/json">.*?</script>',
                  lambda _: blob, html, count=1, flags=re.S)
else:
    html = html.replace('<script id="explaindata"', blob + '\n<script id="explaindata"', 1)
open(HTML, "w", encoding="utf-8").write(html)

print(f"{len(subjects)} subjects -> {OUT} ({os.path.getsize(OUT):,} bytes), injected into {HTML}\n")
hdr = f"{'#':>3} {'subject':<32} {'blue':>5}{'dec':>5}{'trade':>6}{'tbl':>5}{'traps':>6}{'lim':>5}{'integ':>6}"
print(hdr)
gaps = {}
for k in sorted(subjects, key=lambda x: int(x)):
    s = subjects[k]
    c = s["coverage"]
    print(f"{s['i']:>3} {s['nm'][:32]:<32} {c['blueprint']:>5}{c['decision']:>5}{c['tradeoffs']:>6}"
          f"{c['guideTables']:>5}{c['traps']:>6}{c['limits']:>5}{c['integrations']:>6}")
    for field, n in c.items():
        if n == 0:
            gaps.setdefault(field, []).append(s["i"])
print("\nGAPS (rendered as 'not yet authored', never padded):")
for field, ids in sorted(gaps.items()):
    print(f"  {field:<12} missing in {len(ids)} subjects: {ids}")

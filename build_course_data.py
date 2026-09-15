"""Build the Neon Grid course content from the merged SAA-C03 study guide and inject it
into the app. Each subject gets three escalating reads:

  brief  — the spine of the subject plus its must-know call-outs
  deep   — the full write-up, exam nuances, and worked examples with explanations
  recap  — decision rules, scenario cues pulled from the master table, and a glossary

Run:  python3 build_course_data.py          (writes course_data.json and patches the HTML)
"""
import json
import os
import re

MD = "AWS-SAA-C03-Combined.md"
HTML = "neon_academy (4).html"
OUT = "course_data.json"

md = open(MD, encoding="utf-8").read()

topic_pat = re.compile(r'^## (\d+)\. (.+)$', re.M)
sub_pat = re.compile(r'^### (.+)$', re.M)

OVERVIEW = "Topic Overview & Architectural Deep-Dive"
DEEP_PREFIX = "עומק נוסף"
TAKEAWAYS = "Key Takeaways & Exam Tips"
QUESTIONS = "Comprehension / Practice Questions"
ANSWERS = "Detailed Answers & Explanations"


def subsections(body):
    ms = list(sub_pat.finditer(body))
    out = {}
    for i, m in enumerate(ms):
        start, end = m.end(), (ms[i + 1].start() if i + 1 < len(ms) else len(body))
        out[m.group(1).strip()] = body[start:end].strip()
    return out


def blocks(text):
    return [b.strip() for b in re.split(r'\n\s*\n', text.strip()) if b.strip()]


def trim_to(text, budget, floor=0):
    """Whole blocks up to a budget. `floor` keeps taking blocks — even one that overshoots —
    until the summary is actually substantial, so a subject whose first block is a big table
    still gets a real briefing instead of one stray sentence."""
    out, total = [], 0
    for b in blocks(text):
        if out and total + len(b) > budget and total >= floor:
            break
        out.append(b)
        total += len(b) + 2
    return "\n\n".join(out)


# ---------------------------------------------------------------- shared reference data
def parse_table(text):
    """Return [(left, right)] for every two-column markdown row in text."""
    rows = []
    for line in text.split("\n"):
        if not line.strip().startswith("|"):
            continue
        if re.match(r'^\s*\|[\s:|-]+\|?\s*$', line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] and not cells[0].lower().startswith(("if the scenario", "keyword", "term")):
            rows.append((cells[0], cells[1]))
    return rows


glossary_block = md.split("## Master Glossary")[-1] if "## Master Glossary" in md else ""
GLOSSARY = parse_table(glossary_block)

scenario_block = ""
m = re.search(r'## Master Scenario Table.*?(?=\n## Exam-Day Strategy|\n## Master Glossary)', md, re.S)
if m:
    scenario_block = m.group(0)
SCENARIOS = parse_table(scenario_block)

# terms that match almost any subject would add noise rather than signal
STOP_TERMS = {"aws", "region", "availability zone", "iam", "vpc", "s3", "ec2", "kms", "cloudwatch"}


def term_count(term, haystack_lower):
    """How many times a term really appears. Counting rather than testing presence is what
    keeps 'petabyte data warehouse → Redshift' out of the decoupling subject, where Redshift
    is mentioned once in passing."""
    t = term.lower().strip()
    if len(t) < 3 or t in STOP_TERMS:
        return 0
    parts = [p.strip() for p in re.split(r'[/,]| or ', t) if len(p.strip()) >= 3]
    return sum(len(re.findall(r'(?<![a-z0-9])' + re.escape(p) + r'(?![a-z0-9])', haystack_lower))
               for p in parts)


def glossary_for(text, limit=16):
    low = text.lower()
    scored = [(term_count(t, low), t, d) for t, d in GLOSSARY]
    strong = [(n, t, d) for n, t, d in scored if n >= 2]
    if len(strong) < 6:                                   # thin subject — accept single mentions
        strong = [(n, t, d) for n, t, d in scored if n >= 1]
    strong.sort(key=lambda x: (-x[0], -len(x[1])))
    return [(t, d) for _, t, d in strong[:limit]]


def scenarios_for(text, limit=14):
    """Score a scenario row by how densely this subject actually discusses its answer."""
    low = text.lower()
    scored, seen = [], set()
    for cue, ans in SCENARIOS:
        if ans in seen:
            continue
        # the answer's own vocabulary decides the match, not the cue wording
        terms = [t for t, _ in GLOSSARY if term_count(t, ans.lower())]
        weight = max([term_count(t, low) for t in terms] or [0])
        if not terms:                                     # no glossary term — fall back to the answer text
            weight = term_count(ans, low)
        if weight >= 2:
            seen.add(ans)
            scored.append((weight, cue, ans))
    scored.sort(key=lambda x: -x[0])
    return [(c, a) for _, c, a in scored[:limit]]


def md_table(header, rows):
    if not rows:
        return ""
    body = "\n".join("| " + a.replace("|", "/") + " | " + b.replace("|", "/") + " |" for a, b in rows)
    return "| " + header[0] + " | " + header[1] + " |\n|---|---|\n" + body


def worked_examples(subs):
    """Pair each practice question with its explanation so the deep read teaches, not just tests."""
    qs, ans = subs.get(QUESTIONS, ""), subs.get(ANSWERS, "")
    if not qs or not ans:
        return ""
    out = ["### Worked examples", "",
           "Read the scenario, decide your answer, then check the reasoning underneath it.", ""]
    q_blocks = re.split(r'\n(?=\*\*Q\d+\.)', qs.strip())
    a_map = {}
    for blk in re.split(r'\n(?=\*\*Q\d+ —)', ans.strip()):
        mm = re.match(r'\*\*Q(\d+)', blk.strip())
        if mm:
            a_map[mm.group(1)] = blk.strip()
    for blk in q_blocks:
        mm = re.match(r'\*\*Q(\d+)\.', blk.strip())
        if not mm:
            continue
        out.append(blk.strip())
        out.append("")
        if mm.group(1) in a_map:
            out.append(a_map[mm.group(1)])
            out.append("")
    return "\n".join(out).strip()


topics = list(topic_pat.finditer(md))
courses = []
for i, m in enumerate(topics):
    num = int(m.group(1))
    if num > 23:
        continue
    name = m.group(2).strip()
    start = m.end()
    end = topics[i + 1].start() if i + 1 < len(topics) else len(md)
    subs = subsections(md[start:end])

    overview = subs.get(OVERVIEW, "").strip()
    deep_key = next((k for k in subs if k.startswith(DEEP_PREFIX)), None)
    deep = subs.get(deep_key, "").strip() if deep_key else ""
    recap = subs.get(TAKEAWAYS, "").strip()
    subject_text = overview + "\n" + deep

    # --- brief: opening explanation, then every must-know call-out in the subject ---
    intro = trim_to(overview, 1900, floor=1500)
    callouts = [b for b in blocks(overview) if b.startswith(">") and b not in intro]
    if not callouts and deep:
        callouts = [b for b in blocks(deep) if b.startswith(">")]
    brief_parts = [intro]
    if callouts:
        brief_parts.append("### Must know\n\n" + "\n\n".join(callouts[:3]))
    brief = "\n\n".join(brief_parts)

    # --- deep: the whole subject, exam nuances, then worked examples ---
    deep_parts = [overview]
    if deep:
        deep_parts.append("### Exam nuances and common mistakes\n\n" + deep)
    wx = worked_examples(subs)
    if wx:
        deep_parts.append(wx)
    full = "\n\n".join(deep_parts)

    # --- recap: decision rules + scenario cues + the glossary for this subject ---
    recap_parts = ["### Decision rules\n\n" + recap] if recap else []
    cues = scenarios_for(subject_text)
    if cues:
        recap_parts.append("### Scenario cues — if you see this, think this\n\n" +
                           md_table(("If the question says…", "Think…"), cues))
    gloss = glossary_for(subject_text)
    if gloss:
        recap_parts.append("### Glossary for this subject\n\n" +
                           md_table(("Term", "What it means"), gloss))
    recap_full = "\n\n".join(recap_parts)

    if len(full) - len(brief) < 600:
        brief = trim_to(overview, 900, floor=700)

    courses.append({"i": num - 1, "nm": name, "brief": brief, "deep": full, "recap": recap_full})

data = {"courses": courses}
json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# ---------------------------------------------------------------- inject into the app
html = open(HTML, encoding="utf-8").read()
blob = '<script id="coursedata" type="application/json">' + open(OUT, encoding="utf-8").read() + '</script>'
if '<script id="coursedata"' in html:
    html = re.sub(r'<script id="coursedata" type="application/json">.*?</script>', lambda _: blob, html, count=1, flags=re.S)
else:
    html = html.replace('<script id="data" type="application/json">', blob + '\n<script id="data" type="application/json">', 1)
open(HTML, "w", encoding="utf-8").write(html)

print(f"glossary terms parsed: {len(GLOSSARY)} · scenario rows parsed: {len(SCENARIOS)}")
print(f"{len(courses)} courses -> {OUT} ({os.path.getsize(OUT):,} bytes) and injected into {HTML}")
print(f"{'#':>3} {'subject':<44} {'brief':>7} {'deep':>7} {'recap':>7}")
for c in courses:
    print(f"{c['i']:>3} {c['nm'][:44]:<44} {len(c['brief']):>7} {len(c['deep']):>7} {len(c['recap']):>7}")

#!/usr/bin/env python3
"""Repair the OCR damage in the question bank.

These questions were scraped out of PDFs and the scrape left wreckage that a reader
trips over mid-sentence: a stray period after a function word ("to. an Amazon S3
bucket"), an apostrophe where a space belongs ("Use'an"), two words run together
("inthe", "AmazonEC2"), a hyphen for a space ("second-Region").

Each rule below is narrow on purpose. "cross-Region" is a real AWS term, so the
hyphen rule only fires after a function word or an ordinal; abbreviations keep
their periods. BANKV is a written constant, not a hash of the bank, so repairing
the text here does NOT reset anyone's progress.

Run once; index.html is the source of truth afterwards.
"""
import json, re, pathlib

PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
m = re.search(r'(<script id="data" type="application/json">)(.*?)(</script>)', s, re.S)
assert m, "question bank not found"
data = json.loads(m.group(2))

FUNC = "to|in|on|up|a|an|of|for|and|as|at|the|has|all|set|use|or|is|be|by|it|its|that|this|with|from"
VERB = ("Use|Create|Configure|Deploy|Set|Store|Move|Enable|Assign|Attach|Launch|Add|Run|Turn"
        "|Update|Migrate|Install|Apply|Modify|Restore|Copy|Send|Grant|Write|Read|Build|Change")
LEFT = "to|in|on|at|of|a|an|the|and|or|from|with|second|third|first|new|same|other|single"

RULES = [
    # "…and to. query on CreateImage" — a period that ends nothing
    (re.compile(r"(?<![.\w])(" + FUNC + r")\.(\s+)(?=[a-z])"), r"\1\2"),
    # "Use. an Amazon EC2 instance" — same, after the imperative that opens most options
    (re.compile(r"\b(" + VERB + r")\.\s+(?=[A-Za-z])"), r"\1 "),
    # "Use'an", "database'to" — the scrape put an apostrophe where the space was
    (re.compile(r"\b([A-Za-z]{2,})'(?=(?:an|a|the|to|in|on|and|or|with|for)\b)"), r"\1 "),
    # "inthe", "onan", "tothe" — two words with the space lost between them
    (re.compile(r"\b(in|on|to|of|for|with|and|from)(the|a|an|this|that|each|their|its)\b"), r"\1 \2"),
    # "AmazonEC2", "AWSEC2" — and "ofAWS", "usingAWS"
    (re.compile(r"\b(Amazon|AWS)(EC2|S3|RDS|VPC|SQS|SNS|IAM|EBS|EFS|ECS|EKS|KMS|CloudWatch"
                r"|CloudFront|DynamoDB|Lambda|Route)\b"), r"\1 \2"),
    (re.compile(r"\b([a-z]{2,})(Amazon|AWS)\b"), r"\1 \2"),
    # "second-Region", "to-S3" — but never "cross-Region", which is the real term
    (re.compile(r"\b(" + LEFT + r")-(?=(?:Region|Availability|Amazon|AWS|VPC|EC2|S3)\b)"), r"\1 "),
    # "S3.Standard-Infrequent", "(S3.One Zone-IA)" — a lost space INSIDE a product name.
    # This has to run before the sentence rule below, which would otherwise punctuate it.
    (re.compile(r"\b(S3|EC2|EBS|EFS|RDS)\.(?=(?:One|Standard|Glacier|Lifecycle|Intelligent"
                r"|Express|Transfer|Select|Outposts)\b)"), r"\1 "),
    # "Amazon. Kinesis Agent", "AWS. Lambda function" — a period dropped into a service name.
    # Only before a name we can list: "migrating to AWS. The company…" is a real sentence, and
    # "AWS. Config detects" must be fixed while "on AWS. Configure the…" must not, so the
    # service names are matched whole.
    (re.compile(r"\b(Amazon|AWS)\.\s+(?=(?:Kinesis|Lambda|QuickSight|RDS|WAF|Config|KMS|ECS"
                r"|EC2|S3|CloudFront|CloudWatch|CloudTrail|DynamoDB|Redshift|Athena|Glue|SNS|SQS"
                r"|IAM|VPC|Cost|Systems|Certificate|Managed|Snow|Transit|Compute|Storage|Identity"
                r"|Secrets|Step|Direct|Site|Backup|Batch|Fargate|Aurora|Route)\b)"), r"\1 "),
    # and a period after Amazon/AWS followed by a lowercase word is always damage
    (re.compile(r"\b(Amazon|AWS)\.\s+(?=[a-z])"), r"\1 "),
    # two stray backslashes, both standing in for a space
    (re.compile(r"\\+(?=[A-Za-z])"), " "),
    # "AmazonEC2.The consumer application" — a sentence period with no space after it
    (re.compile(r"([a-z0-9])\.(?=[A-Z][a-z])"), r"\1. "),
]


def fix(t):
    for pat, rep in RULES:
        t = pat.sub(rep, t)
    return t


changes = []
nopt = nstem = 0
for qi, q in enumerate(data["questions"]):
    f = fix(q["q"])
    if f != q["q"]:
        changes.append((qi, "stem", q["q"], f)); q["q"] = f; nstem += 1
    for p in q["o"]:
        f = fix(p[1])
        if f != p[1]:
            changes.append((qi, p[0], p[1], f)); p[1] = f; nopt += 1

# show only the words that actually moved, so the diff is checkable by eye
def diffwords(a, b):
    aw, bw = a.split(), b.split()
    import difflib
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, aw, bw).get_opcodes():
        if tag != "equal":
            out.append(" ".join(aw[i1:i2]) + "  →  " + " ".join(bw[j1:j2]))
    return out

print("repaired %d option texts and %d stems\n" % (nopt, nstem))
shown = 0
for qi, where, a, b in changes:
    for d in diffwords(a, b):
        if shown < 30:
            print("  q%-4d %-4s %s" % (qi, where, d)); shown += 1

import sys
if "--apply" not in sys.argv:
    print("\n(dry run — pass --apply to write)")
    sys.exit()

s = s[:m.start(2)] + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + s[m.end(2):]
PAGE.write_text(s, encoding="utf-8")
print("\nwritten · page %.2f MB" % (len(s) / 1e6))

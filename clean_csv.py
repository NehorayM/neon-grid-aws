#!/usr/bin/env python3
"""Clean the exam-dump CSV into a reviewable, stable question list.

The source is OCR'd, so it carries a small set of mechanical injuries: S3 read as
$3, Standard-IA as Standard-lA, hyphens inserted where a space belongs, and missing
spaces after a full stop. Everything here is a targeted repair — nothing rewrites the
meaning of a question, because the answer review depends on reading exactly what the
candidate would read.
"""
import csv, json, re, pathlib, collections

HERE = pathlib.Path(__file__).resolve().parent
# the source file lives in the repo so the pipeline reruns without the original download
SRC = HERE / "qsrc" / "aws_saa_questions_full.csv"
OUT = HERE / "qsrc" / "questions_clean.json"

# hyphens that belong in the text and must survive the repair pass
KEEP_HYPHEN = {
    "on-premises", "on-premise", "on-demand", "site-to", "point-in", "text-to", "end-to",
    "service-to", "up-to", "sign-in", "sign-on", "built-in", "end-of", "on-failure",
    "proof-of", "opt-in", "opt-out", "log-in", "check-in", "run-on", "add-on", "back-of",
    "out-of", "in-transit", "in-place", "in-memory", "in-flight", "to-live", "write-once",
}

FIXES = [
    (r"\$3\b", "S3"),                       # Amazon $3 -> Amazon S3
    (r"\bStandard-lA\b", "Standard-IA"),
    (r"\bZone-lA\b", "Zone-IA"),
    (r"\bS3-lA\b", "S3-IA"),
    (r"\bUsea\b", "Use a"),
    (r"\bUsean\b", "Use an"),
    (r"\bCreatea\b", "Create a"),
    (r"\bCreatean\b", "Create an"),
    (r"\bConfigurea\b", "Configure a"),
    (r"\bqueueInvoke\b", "queue. Invoke"),
    (r"\bcreateVolume\b", "CreateVolume"),
]

SMART = {"’": "'", "‘": "'", "“": '"', "”": '"', "—": " - ",
         "–": "-", " ": " ", "«": '"', "»": '"', "…": "..."}


def repair(s):
    s = s or ""
    for k, v in SMART.items():
        s = s.replace(k, v)
    for pat, rep in FIXES:
        s = re.sub(pat, rep, s)
    # a hyphen joining two words where one is a function word is an OCR'd space
    def unhyphen(m):
        w = m.group(0)
        return w if w.lower() in KEEP_HYPHEN else w.replace("-", " ")
    s = re.sub(r"\b(?:a|an|the|to|and|or|of|in|on|for|with|from|is|are|be|as|at|by|"
               r"use|uses|used|create|creates|created|configure|configures|set|store|"
               r"stores|enable|enables|generate|generates|provision|provisions|mount|"
               r"mounts|invoke|invokes|import|imports|sign|make|move|attach|add)"
               r"-[A-Za-z]{2,}\b", unhyphen, s, flags=re.I)
    s = re.sub(r"\b[A-Za-z]{2,}-(?:a|an|the|to|and|or|of|in|on|for|with|from)\b",
               unhyphen, s, flags=re.I)
    # a full stop immediately followed by a capital is a lost space
    s = re.sub(r"(?<=[a-z])\.(?=[A-Z][a-z])", ". ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# OCR ran options together in about 240 rows: the text of the next option landed at the
# end of the previous one, behind a marker such as "B.-", "B_-", "|-B.-" or "\u00a9." (which is
# how "C." was read). Splitting them back apart is safe, because the marker only ever
# appears where the next option began. Several options can be merged into one cell, so
# this runs until it stops finding markers.
# a marker must follow whitespace or OCR junk, never sit inside a word; the letter itself
# may have been read as a lookalike glyph
MARK = re.compile(r"(?<![A-Za-z0-9])[\s|\\\"~.,()\u2014\-]*[\u00a9@*]?\s*([A-F\u00a9\u00a3\u20ac3])\s*[._:\-]+\s*-?\s*")
LOOKALIKE = {"C": {"C", "\u00a9"}, "E": {"E", "\u00a3", "\u20ac", "3"}}


def split_off(text, nxt):
    want = LOOKALIKE.get(nxt, {nxt})
    for m in MARK.finditer(text):
        if m.group(1) in want and m.start() >= 15:
            head, tail = text[:m.start()].strip(" .,-|\\\"~"), text[m.end():].strip()
            # an option never starts mid-sentence: a lower-case tail means the marker was
            # part of the text, such as the "3" in "a 3-year commitment"
            if len(head) >= 12 and len(tail) >= 6 and not tail[0].islower():
                return head, tail
    return None


def unmerge(opts):
    for _ in range(4):
        letters = [o[0] for o in opts]
        expected = list("ABCDEF")[:len(letters) + 1]
        missing = [c for c in expected if c not in letters]
        if not missing:
            break
        miss = missing[0]
        host = next((o for o in opts if o[0] == chr(ord(miss) - 1)), None)
        if not host:
            break
        r = split_off(host[1], miss)
        if not r:
            break
        host[1] = r[0]
        opts = sorted(opts + [[miss, r[1]]], key=lambda o: o[0])
    return opts


# the generic repair cannot place a fragment whose letter marker was lost entirely
MANUAL = {
    # the transcription reversed the two services in option A, which inverts the whole
    # question; the stem asks for UI to DynamoDB and data services to S3
    238: {"a": "Create separate Kubernetes service accounts for the UI and data services to assume "
               "an IAM role. Use IAM Roles for Service Accounts (IRSA) to provide access to the EKS "
               "Pods for the UI to DynamoDB and the EKS Pods for the data services to Amazon S3."},
    # the marker before option E was lost, leaving two options in one cell
    604: {"d": "Do not restart the RDS for PostgreSQL instances after the configuration update.",
          "add": [["E", "Configure the RDS for PostgreSQL instances to encrypt traffic by "
                        "using a parameter group."]]},
    217: {"d": "Purchase an EC2 Instance Savings Plan for Amazon EC2 and Fargate.",
          "add": [["E", "Purchase a SageMaker Savings Plan."]]},
    # the label of the lost option D was glued to the front of option C's cell
    # the marker before option F was lost, leaving "... transit VIF. CF. Share the ..." in one cell
    # the marker before option F was lost, leaving "... application tier- UF. Configure ..." in one cell
    # OCR duplicated option C into option D; only one of the two can be a real choice
    1200: {"del": ["D"]},
    1039: {"e": "Configure the security group for the database tier to allow inbound Microsoft SQL "
                "Server traffic from the security group for the application tier.",
           "add": [["F", "Configure the security group for the application tier to allow outbound "
                         "HTTPS traffic and Microsoft SQL Server traffic to the security group for "
                         "the web tier."]]},
    962: {"a": "Provision only private subnets. Open the necessary route on the transit gateway and "
               "customer gateway to allow outbound internet traffic from AWS to flow through NAT "
               "services that run in the data center.",
          "e": "Create a Direct Connect gateway and a transit gateway in the central network account. "
               "Attach the transit gateway to the Direct Connect gateway by using a transit VIF.",
          "add": [["F", "Share the transit gateway with other accounts. Attach VPCs to the transit "
                        "gateway."]]},
    877: {"c": "Create an AWS Batch job that runs every 15 minutes. Configure the Batch job to use "
               "the S3 CopyObject API to copy new documents to an S3 bucket in a second Region."},
    144: {"a": "Amazon DynamoDB", "add": [["B", "AWS Lambda"], ["E", "Amazon Elastic Kubernetes Service (Amazon EKS)"]],
          "d": "Amazon EC2"},
}
DROP = {
    105: "the policy JSON the question depends on did not survive OCR",
    318: "option B, the correct answer, is unrecoverable",
    433: "option B is missing and the recorded answer needs it",
    947: "the 'invoke a Lambda function from the queue' option, one of the three answers, was lost",
    954: "a CompTIA Security+ question, not an AWS one",
    955: "a CompTIA Security+ question, not an AWS one",
    956: "a CompTIA Security+ question, not an AWS one",
    1211: "option A, one of the three answers, was lost with its marker",
}


def main():
    rows = list(csv.DictReader(SRC.open(encoding="utf-8")))
    out, dropped, seen = [], [], {}
    for r in rows:
        item = int(r["item_number"])
        q = repair(r["question_text"])
        opts = []
        for letter in "abcdef":
            t = repair(r.get("option_" + letter) or "")
            if t:
                opts.append([letter.upper(), t])
        if item in DROP:
            dropped.append({"item": item, "why": DROP[item], "q": q[:120]})
            continue
        opts = [o for o in opts if len(re.sub(r"[^A-Za-z0-9]", "", o[1])) > 2]  # ") C)." and friends
        opts = unmerge(opts)
        if item in MANUAL:
            fix = MANUAL[item]
            for o in opts:
                if o[0].lower() in fix:
                    o[1] = fix[o[0].lower()]
            opts = [o for o in opts if o[0] not in fix.get("del", [])]
            have = {o[0] for o in opts}
            opts = sorted(opts + [list(x) for x in fix.get("add", []) if x[0] not in have],
                          key=lambda o: o[0])
        key = re.sub(r"\W+", "", q.lower())[:400]
        if len(q) < 80 or len(opts) < 3:
            dropped.append({"item": item, "why": "incomplete after OCR", "q": q[:120]})
            continue
        if key in seen:
            dropped.append({"item": item, "why": f"duplicate of item {seen[key]}", "q": q[:120]})
            continue
        seen[key] = item
        given = [c.strip().upper() for c in (r["correct_answer"] or "").split(",") if c.strip()]
        letters = {o[0] for o in opts}
        if any(g not in letters for g in given):
            given = []                      # answer points at an option that is not there
        out.append({"item": item, "exam": r["exam_type"], "n": int(r["question_number"]),
                    "q": q, "o": opts, "csv": given})
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=0))
    print(f"kept {len(out)}, dropped {len(dropped)}")
    for d in dropped:
        print(f"   - item {d['item']}: {d['why']}")
    print(f"   with a CSV answer: {sum(1 for x in out if x['csv'])}")
    print(f"   needing an answer: {sum(1 for x in out if not x['csv'])}")
    print(f"   multi-answer: {sum(1 for x in out if len(x['csv']) > 1)}")
    print(f"   option counts: {dict(collections.Counter(len(x['o']) for x in out))}")


if __name__ == "__main__":
    main()

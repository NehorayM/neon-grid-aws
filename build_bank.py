#!/usr/bin/env python3
"""Turn the reviewed CSV questions into the site's question bank.

Reads  qsrc/questions_clean.json  (cleaned question text, from clean_csv.py)
       qsrc/answers.py            (the reviewed answer key, V and NOTES)
Writes qsrc/bank.json             ({"sections","short","questions"})

Every question is assigned to one of the 23 course sections so that
practise-by-sector, the readiness report and the Learn mode's
"Practise this subject" button keep working.
"""
import importlib.util
import json
import pathlib
import re
import sys
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "qsrc" / "questions_clean.json"
KEY = HERE / "qsrc" / "answers.py"
OUT = HERE / "qsrc" / "bank.json"

SECTIONS = [
    "IAM & AWS CLI",
    "EC2 Fundamentals",
    "EC2 - Solutions Architect Associate Level",
    "EC2 Instance Storage (EBS & EFS)",
    "High Availability & Scalability: ELB & ASG",
    "RDS + Aurora + ElastiCache",
    "Route 53",
    "Amazon S3",
    "CloudFront & Global Accelerator",
    "AWS Storage Extras (Snow, FSx, Storage Gateway, DataSync)",
    "Decoupling: SQS, SNS, Kinesis, Amazon MQ",
    "Containers: ECS, Fargate, ECR & EKS",
    "Serverless: Lambda, DynamoDB, API Gateway, Cognito",
    "Databases in AWS",
    "Data & Analytics",
    "Machine Learning",
    "Monitoring & Audit: CloudWatch, CloudTrail, Config",
    "IAM Advanced: Organizations, Identity Center, STS",
    "Security & Encryption: KMS, Secrets Manager, WAF, Shield",
    "Networking: VPC",
    "Disaster Recovery & Migrations",
    "Other Services",
    "Well-Architected Framework & Cost Management",
]
SHORT = [
    "IAM & CLI", "EC2 Fundamentals", "EC2 (SA level)", "EBS & EFS", "ELB & ASG",
    "RDS, Aurora, ElastiCache", "Route 53", "Amazon S3", "CloudFront & GA",
    "Storage extras", "SQS, SNS, Kinesis", "Containers", "Serverless",
    "Databases in AWS", "Data & Analytics", "Machine Learning", "Monitoring & audit",
    "IAM advanced", "Security & encryption", "VPC & networking", "DR & migrations",
    "Other Services", "Well-Architected & cost",
]

# Each rule is (section, weight, regex). The section with the highest total
# weight wins; a tie falls to the earlier rule in this list. Weights are rough
# "how much does this phrase pin the subject down" scores, so a passing mention
# of S3 never outvotes a question that is actually about Route 53 records.
RULES = [
    # 0 IAM & AWS CLI
    (0, 6, r"\bIAM role\b|\binstance profile\b|\bIAM user\b|\bIAM polic|\btrust policy\b|\bassume the role\b|\baccess key"),
    (0, 3, r"\bleast privilege\b|\bprincipal\b|\bresource-based polic"),
    # 1 EC2 Fundamentals
    (1, 4, r"\bsecurity group\b|\buser data\b|\bAmazon Machine Image\b|\bAMI\b|\belastic IP\b"),
    (1, 3, r"\bkey pair\b|\binstance type\b|\binstance family\b"),
    # 2 EC2 - SA level (purchasing options, placement, tenancy, hibernate)
    (2, 7, r"\bSpot (Instance|Fleet)|\bReserved Instance|\bSavings Plan|\bOn-Demand (Instance|Capacity Reservation)|\bDedicated (Host|Instance)"),
    (2, 7, r"\bplacement group\b|\bhibernat|\bCompute Optimizer\b|\bGraviton\b|\bElastic Fabric Adapter\b|\bEFA\b"),
    # 3 EBS & EFS
    (3, 7, r"\bEBS\b|\bElastic Block Store\b|\bgp2\b|\bgp3\b|\bio1\b|\bio2\b|\bProvisioned IOPS\b|\bsnapshot"),
    (3, 7, r"\bEFS\b|\bElastic File System\b|\binstance store\b|\bfast snapshot restore\b"),
    # 4 ELB & ASG
    (4, 7, r"\bAuto Scaling\b|\bscaling polic|\bscheduled scaling\b|\btarget tracking\b|\bstep scaling\b"),
    (4, 7, r"\bApplication Load Balancer\b|\bNetwork Load Balancer\b|\bGateway Load Balancer\b|\bALB\b|\bNLB\b|\btarget group\b|\bsticky session"),
    # 5 RDS + Aurora + ElastiCache
    (5, 8, r"\bAurora\b|\bAmazon RDS\b|\bRDS for\b|\bRDS DB instance\b|\bread replica|\bMulti-AZ\b|\bRDS Proxy\b"),
    (5, 8, r"\bElastiCache\b|\bMemcached\b|\bRedis\b"),
    # 6 Route 53
    (6, 9, r"\bRoute 53\b|\bhosted zone\b|\brouting policy\b|\bDNS\b|\bResolver (endpoint|rule)|\bCNAME\b|\balias record\b"),
    # 7 Amazon S3
    (7, 7, r"\bS3 bucket\b|\bAmazon S3\b|\bS3 Lifecycle\b|\bS3 Glacier\b|\bObject Lock\b|\bS3 Intelligent-Tiering\b|\bpresigned URL"),
    (7, 5, r"\bStandard-Infrequent Access\b|\bOne Zone-IA\b|\bS3 Replication\b|\bCross-Region Replication\b|\bS3 Inventory\b|\bStorage Lens\b"),
    # 8 CloudFront & Global Accelerator
    (8, 9, r"\bCloudFront\b|\bGlobal Accelerator\b|\bLambda@Edge\b|\bedge-optimized\b|\bTransfer Acceleration\b|\borigin access control\b"),
    # 9 Storage extras
    (9, 11, r"\bSnowball\b|\bSnowcone\b|\bSnowmobile\b|\bFSx\b|\bStorage Gateway\b|\bFile Gateway\b|\bVolume Gateway\b|\bTape Gateway\b|\bDataSync\b|\bTransfer Family\b|\bOutposts\b"),
    # 10 Decoupling
    (10, 9, r"\bSQS\b|\bSimple Queue Service\b|\bSNS\b|\bSimple Notification Service\b|\bKinesis\b|\bAmazon MQ\b|\bEventBridge\b|\bData Firehose\b|\bdead-letter queue\b|\bFIFO queue\b"),
    # 11 Containers
    (11, 9, r"\bECS\b|\bElastic Container\b|\bFargate\b|\bECR\b|\bEKS\b|\bKubernetes\b|\bDocker\b|\bcontainer image\b|\btask definition\b"),
    # 12 Serverless
    (12, 9, r"\bLambda function\b|\bAWS Lambda\b|\bDynamoDB\b|\bAPI Gateway\b|\bCognito\b|\bStep Functions\b|\bprovisioned concurrency\b|\breserved concurrency\b|\bSnapStart\b"),
    # 13 Databases in AWS
    (13, 8, r"\bRedshift\b|\bDocumentDB\b|\bNeptune\b|\bKeyspaces\b|\bTimestream\b|\bQLDB\b|\bMemoryDB\b|\bAthena\b"),
    # 14 Data & Analytics
    (14, 8, r"\bAWS Glue\b|\bLake Formation\b|\bdata lake\b|\bAmazon EMR\b|\bQuickSight\b|\bQuick Sight\b|\bOpenSearch\b|\bApache Flink\b|\bApache Spark\b|\bzero-ETL\b|\bETL\b"),
    # 15 Machine Learning
    (15, 9, r"\bSageMaker\b|\bmachine learning\b|\bRekognition\b|\bComprehend\b|\bTranscribe\b|\bPolly\b|\bTextract\b|\bForecast\b|\bBedrock\b|\bgenerative"),
    # 16 Monitoring & audit
    (16, 8, r"\bCloudWatch\b|\bCloudTrail\b|\bAWS Config\b|\bX-Ray\b|\bmetric filter\b|\bflow logs\b|\bAudit Manager\b|\bTrusted Advisor\b"),
    # 17 IAM advanced
    (17, 9, r"\bOrganizations\b|\bservice control policy\b|\bSCP\b|\bIAM Identity Center\b|\bSingle Sign-On\b|\bAWS SSO\b|\bAWS STS\b|\bControl Tower\b|\borganizational unit\b|\bOU\b|\bAD FS\b|\bDirectory Service\b|\bActive Directory\b|\bSAML\b"),
    # 18 Security & encryption
    (18, 9, r"\bKMS\b|\bKey Management Service\b|\bSecrets Manager\b|\bAWS WAF\b|\bweb ACL\b|\bShield\b|\bGuardDuty\b|\bMacie\b|\bInspector\b|\bSecurity Hub\b|\bCloudHSM\b|\bencrypt|\bParameter Store\b|\bcertificate\b|\bACM\b"),
    # 19 VPC & networking
    (19, 9, r"\bVPC\b|\bsubnet\b|\bNAT gateway\b|\binternet gateway\b|\bDirect Connect\b|\btransit gateway\b|\bVPC endpoint\b|\bPrivateLink\b|\bSite-to.Site VPN\b|\bClient VPN\b|\bnetwork ACL\b|\bVPC peering\b|\bCIDR\b|\bvirtual interface\b|\bVIF\b"),
    # 20 DR & migrations
    (20, 9, r"\bdisaster recovery\b|\brecovery time objective\b|\brecovery point objective\b|\bRTO\b|\bRPO\b|\bpilot light\b|\bwarm standby\b|\bfail ?over\b|\bDatabase Migration Service\b|\bAWS DMS\b|\bSchema Conversion Tool\b|\bMigration Hub\b|\bApplication Discovery\b|\bAWS Backup\b"),
    (20, 4, r"\bmigrate\b|\bmigration\b|\brehost\b|\breplatform\b"),
    # 21 Other services
    (21, 7, r"\bElastic Beanstalk\b|\bCloudFormation\b|\bSystems Manager\b|\bAmplify\b|\bAppSync\b|\bAWS Batch\b|\bApp Runner\b|\bCodeDeploy\b|\bCodePipeline\b|\bService Catalog\b|\bResource Access Manager\b|\bAWS RAM\b|\bWorkSpaces\b|\bAppStream\b"),
    # 22 Well-Architected & cost
    (22, 8, r"\bCost Explorer\b|\bAWS Budgets\b|\bCost and Usage Report\b|\bbilling\b|\bcost allocation tag|\bdiscount sharing\b|\bWell-Architected\b|\bconsolidated billing\b"),
]
RULES = [(sec, w, re.compile(rx, re.I)) for sec, w, rx in RULES]

# A few questions are really about one service that a broad rule would grab
# first; these say the last word.
FORCE = [
    (7, re.compile(r"storage class|S3 Lifecycle|Object Lock|bucket policy|presigned URL", re.I)),
]


def classify(q):
    """Return (section, score, runner-up score) for one question."""
    stem = q["q"]
    opts = " ".join(t for _, t in q["o"])
    score = Counter()
    for sec, w, rx in RULES:
        hits_stem = len(rx.findall(stem))
        hits_opts = len(rx.findall(opts))
        if hits_stem or hits_opts:
            # the stem says what the question is about; options are a weaker hint
            score[sec] += w * min(hits_stem, 3) + (w // 2) * min(hits_opts, 3)
    if not score:
        # nothing matched: a plain EC2 question belongs with the fundamentals,
        # anything else falls to the catch-all section
        return (1 if re.search(r"\bEC2\b|\bAmazon Machine Image\b", stem, re.I) else 21), 0, 0
    ranked = score.most_common()
    top = ranked[0][1]
    if top < 6 and re.search(r"\bEC2 instance", stem, re.I):
        return 1, top, top   # weak signal on an EC2 question: call it fundamentals
    # keep rule order as the tie-break so the earlier (more specific) rule wins
    best = min((s for s, v in ranked if v == top), key=lambda s: s)
    return best, top, (ranked[1][1] if len(ranked) > 1 else 0)


def main():
    qs = json.loads(SRC.read_text(encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("answers", KEY)
    key = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(key)
    V = key.V

    out, weak = [], []
    for q in qs:
        letters = [l for l, _ in q["o"]]
        ans = list(V[q["item"]])
        assert ans, f"item {q['item']} has no answer"
        for a in ans:
            assert a in letters, f"item {q['item']}: answer {a} is not an option"
        assert len(set(letters)) == len(letters), f"item {q['item']} repeats an option letter"
        texts = [t.strip().lower() for _, t in q["o"]]
        assert len(set(texts)) == len(texts), f"item {q['item']} repeats an option"
        sec, top, second = classify(q)
        if top - second < 3:
            weak.append((q["item"], sec, top, second))
        out.append({"s": sec, "q": q["q"], "o": [[l, t] for l, t in q["o"]],
                    "a": ans, "v": 1})

    counts = Counter(x["s"] for x in out)
    empty = [i for i in range(len(SECTIONS)) if counts[i] == 0]
    assert not empty, f"sections with no questions: {[SECTIONS[i] for i in empty]}"

    OUT.write_text(json.dumps({"sections": SECTIONS, "short": SHORT, "questions": out},
                              ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {len(out)} questions to {OUT.relative_to(HERE)}")
    for i, name in enumerate(SHORT):
        print(f"  {i:2d} {name:<26} {counts[i]:4d}")
    print(f"  close calls (winning margin < 3): {len(weak)}")
    pos = Counter()
    for x in out:
        for a in x["a"]:
            pos[a] += 1
    total = sum(pos.values())
    print("  answer letters:", {k: f"{v * 100 // total}%" for k, v in sorted(pos.items())})
    print("  answers per question:", dict(Counter(len(x["a"]) for x in out)))
    if "--weak" in sys.argv:
        for w in weak:
            print("   weak:", w)


if __name__ == "__main__":
    main()

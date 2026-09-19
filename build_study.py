#!/usr/bin/env python3
"""Turn the study notes into the site's Study mode.

Reads  qsrc/aws-saa-study-notes-english.md   (prose notes, one ## per topic)
Writes the #studydata blob inside index.html

The notes are flowing prose. Prose alone is hard to revise from, so this adds
what prose cannot carry: comparison tables, decision trees, flows, and the
must-know / exam-trap callouts — authored per topic in EXTRAS below — plus a
few multiple-choice checks per chapter. Blocks use the same vocabulary as the
Learn mode, so both modes render through one renderer.
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "qsrc" / "aws-saa-study-notes-english.md"
PAGE = HERE / "index.html"

# ---------------------------------------------------------------- chapters
# title -> chapter index. Every ## in the notes must appear here or the build
# refuses, so a new topic can never quietly go missing from the app.
CHAPTERS = [
    ("Cloud foundations", "\U0001f30d", "What a Region actually is, how you reach AWS, and who is responsible for what."),
    ("Identity & access", "\U0001f511", "IAM, Organizations, federation — the layer every other question quietly depends on."),
    ("S3 & content delivery", "\U0001faa3", "Object storage, its storage classes, and getting bytes close to the user."),
    ("EC2 compute", "\U0001f5a5️", "Instances, how you pay for them, and how you place them."),
    ("Block & file storage", "\U0001f4be", "EBS, instance store, EFS and FSx — and when each one is the answer."),
    ("Databases", "\U0001f5c3️", "Relational, NoSQL, warehouse and cache, and how to tell them apart under exam pressure."),
    ("DNS & Route 53", "\U0001f9ed", "Record types and the seven routing policies."),
    ("VPC & networking", "\U0001f578️", "Subnets, gateways, peering and the private ways into AWS."),
    ("Load balancing & scaling", "⚖️", "The three load balancers, and making capacity follow demand."),
    ("Decoupling & integration", "\U0001f4e8", "Queues, topics, streams and the patterns built from them."),
    ("Security & encryption", "\U0001f512", "KMS, CloudHSM, secrets, WAF and Shield."),
    ("Serverless & containers", "⚡", "Lambda, ECS, Fargate, EKS — compute you do not patch."),
    ("Management & migration", "\U0001f9f0", "Watching what runs, describing it as code, and moving it in."),
]

SECTION_CH = {
    "Regions, Availability Zones, and Edge Locations": 0,
    "Accessing and Managing AWS": 0,
    "Security and the AWS Shared Responsibility Model": 0,
    "IAM Basics": 1,
    "AWS Organizations and Consolidated Billing": 1,
    "Advanced IAM: AWS Directory Service": 1,
    "Evaluating IAM Policies": 1,
    "Permission Boundaries, Resource Access Manager, and Single Sign-On": 1,
    "Web Identity Federation and Cognito": 1,
    "Amazon S3": 2,
    "AWS DataSync": 2,
    "CloudFront": 2,
    "Snowball and Storage Gateway": 2,
    "Athena versus Macie": 2,
    "Amazon EC2": 3,
    "Security Groups": 3,
    "Spot Instances and Spot Fleets": 3,
    "EC2 Hibernate": 3,
    "Bootstrap Scripts and Instance Metadata": 3,
    "EC2 Placement Groups": 3,
    "High Performance Computing and Data Transfer": 3,
    "Elastic Block Store, EBS": 4,
    "Instance Store": 4,
    "ENI versus Enhanced Networking versus EFA": 4,
    "Amazon Data Lifecycle Manager and Encrypted Root Volumes": 4,
    "EFS and FSx": 4,
    "Databases Overview": 5,
    "RDS Specifics": 5,
    "RDS Encryption": 5,
    "DynamoDB": 5,
    "SimpleDB": 5,
    "Redshift": 5,
    "Aurora": 5,
    "ElastiCache": 5,
    "Database Migration Service": 5,
    "Caching Strategies on AWS": 5,
    "EMR": 5,
    "DNS Basics": 6,
    "Registering a Domain and Route 53 Routing Policies": 6,
    "VPC Basics": 7,
    "VPC Peering": 7,
    "Creating a New VPC": 7,
    "NAT Instances and NAT Gateways": 7,
    "Network ACLs versus Security Groups": 7,
    "VPC Flow Logs": 7,
    "Bastion Hosts": 7,
    "Direct Connect": 7,
    "AWS Global Accelerator and VPC Endpoints": 7,
    "AWS PrivateLink": 7,
    "AWS Transit Gateway": 7,
    "AWS VPN CloudHub": 7,
    "AWS Network Costs": 7,
    "Steps to Create a VPC, Summarized": 7,
    "Load Balancers": 8,
    "Auto Scaling": 8,
    "High Availability with Bastion Hosts": 8,
    "Amazon SQS": 9,
    "Simple Workflow Service": 9,
    "Amazon SNS": 9,
    "Elastic Transcoder and API Gateway": 9,
    "Amazon Kinesis": 9,
    "Event Processing Patterns": 9,
    "AWS WAF": 10,
    "Security: KMS": 10,
    "CloudHSM": 10,
    "Systems Manager Parameter Store and Secrets Manager": 10,
    "AWS Shield": 10,
    "WAF, Revisited": 10,
    "Serverless: AWS Lambda": 11,
    "SAM": 11,
    "ECS": 11,
    "Docker and Containers": 11,
    "Fargate, EKS, and ECR": 11,
    "CloudWatch and CloudTrail": 12,
    "CloudFormation, Elastic Beanstalk, OpsWorks, Glue, and Trusted Advisor": 12,
    "On-Premises Migration Strategies with AWS": 12,
}

T = lambda head, rows, cap=None: dict(t="table", head=head, rows=rows, **({"cap": cap} if cap else {}))
F = lambda nodes, cap=None: dict(t="flow", x=nodes, **({"cap": cap} if cap else {}))
D = lambda rows, cap=None: dict(t="dtree", x=rows, **({"cap": cap} if cap else {}))
K = lambda x: dict(t="key", x=x)
X = lambda x: dict(t="trap", x=x)
N = lambda x: dict(t="note", x=x)
H = lambda x: dict(t="h", x=x)
L = lambda items: dict(t="list", x=items)

# ------------------------------------------------------- authored additions
# What the prose cannot do: put two things side by side, or draw the order of
# events. Keyed by the ## heading they belong under.
EXTRAS = {
"Regions, Availability Zones, and Edge Locations": [
  H("The three scopes, side by side"),
  T(["Scope", "What it is", "What it is for"],
    [["Region", "A geographic area holding several Availability Zones", "Latency, price, service availability, data-residency law"],
     ["Availability Zone", "One or more data centres, isolated power and network", "Surviving the loss of a building without losing the app"],
     ["Edge location", "A small POP, hundreds of them", "Caching content close to the user — CloudFront, Global Accelerator"]]),
  K("Multi-AZ is how you survive a data-centre failure. Multi-Region is how you survive a Region failure — and it always costs more, so the exam only wants it when the question says Region or says the RTO is tiny."),
],
"Security and the AWS Shared Responsibility Model": [
  dict(t="split", cols=[
    {"nm": "AWS — security OF the cloud", "items": ["Physical data centres", "Hardware and the hypervisor", "The global network", "Managed-service patching (RDS engine, Lambda runtime)"]},
    {"nm": "You — security IN the cloud", "items": ["IAM users, roles and policies", "Security groups and NACLs", "Encryption choices and key policies", "Guest OS patching on EC2", "Your own backups"]}]),
  X("On EC2 the guest OS is yours to patch. On RDS it is not. A question that says “patch the operating system” is testing whether you know which side of the line the service sits on."),
],
"IAM Basics": [
  T(["Identity", "Has credentials?", "Use it when"],
    [["User", "Password and/or access keys, long-lived", "A human, or a legacy app that cannot assume a role"],
     ["Group", "No — a container for users", "Attaching one policy to many people"],
     ["Role", "No long-lived credentials; STS mints temporary ones", "EC2, Lambda, another account, a federated identity"]]),
  K("IAM is global, not regional. A user, a role and a policy exist in every Region at once."),
  X("An access key on an EC2 instance is the wrong answer every single time. The answer is an IAM role attached to the instance."),
],
"AWS Organizations and Consolidated Billing": [
  F(["Management account", "Organizational Unit", "Member accounts", "SCP applies to all of them"],
    "An SCP sets the ceiling; it never grants anything on its own."),
  X("An SCP is a permission boundary, not a permission. If the SCP allows an action and the account's IAM policy does not, the action is still denied."),
],
"Amazon S3": [
  H("Storage classes at a glance"),
  T(["Class", "Availability", "First-byte latency", "Reach for it when"],
    [["Standard", "99.99%", "milliseconds", "Active data, unknown access pattern under 30 days"],
     ["Intelligent-Tiering", "99.9%", "milliseconds", "You genuinely cannot predict the pattern; it moves objects for you"],
     ["Standard-IA", "99.9%", "milliseconds", "Infrequent but needs to be there instantly; 30-day minimum"],
     ["One Zone-IA", "99.5%", "milliseconds", "Infrequent AND reproducible — one AZ only"],
     ["Glacier Instant Retrieval", "99.9%", "milliseconds", "Archive you still read now and then"],
     ["Glacier Flexible Retrieval", "99.99%", "minutes to 12 hours", "Archive, retrieval measured in hours is fine"],
     ["Glacier Deep Archive", "99.99%", "12–48 hours", "Compliance archive you hope never to read"]]),
  D([["Needs it back in milliseconds?", "Standard / IA / Instant Retrieval"],
     ["Can wait minutes to hours?", "Flexible Retrieval"],
     ["Can wait half a day?", "Deep Archive"],
     ["Cannot predict the pattern at all?", "Intelligent-Tiering"],
     ["Losing it is survivable and it is cheap to rebuild?", "One Zone-IA"]]),
  H("The four ways to encrypt"),
  T(["Option", "Who holds the key", "Who does the encrypting", "Audit trail of key use"],
    [["SSE-S3", "AWS", "S3", "No"],
     ["SSE-KMS", "You, in KMS", "S3", "Yes — CloudTrail"],
     ["SSE-C", "You, sent with each request", "S3", "No"],
     ["Client-side", "You", "You, before upload", "Whatever you build"]]),
  K("“We must be able to prove who used the key and when” means SSE-KMS. Nothing else gives you that trail."),
  X("Cross-Region Replication needs versioning on both buckets, and it only copies objects written after you turn it on. Existing objects need S3 Batch Replication."),
  X("Object Lock in compliance mode cannot be shortened by anyone, root included. Governance mode can, by a user with the right permission. Ransomware questions want compliance."),
],
"CloudFront": [
  T(["Term", "Meaning"],
    [["Origin", "Where the real content lives — S3, ALB, EC2, or anything on the internet"],
     ["Distribution", "The CDN configuration itself"],
     ["Edge location", "Where the copy is cached"],
     ["OAC / OAI", "Lets only CloudFront read a private S3 bucket"],
     ["Signed URL", "Time-limited access to one file"],
     ["Signed cookie", "Time-limited access to many files"]]),
  K("CloudFront accelerates uploads too — a PUT through an edge location rides the AWS backbone instead of the open internet."),
  X("CloudFront caches. S3 Transfer Acceleration does not cache; it only routes an upload through the nearest edge. A question about downloading the same file repeatedly is CloudFront; a question about uploading large files from far away is Transfer Acceleration."),
],
"Snowball and Storage Gateway": [
  T(["Gateway", "Protocol the on-premises side speaks", "Where the data lands"],
    [["File Gateway", "NFS and SMB", "S3 objects"],
     ["Volume Gateway — stored", "iSCSI", "All data local, snapshots to S3"],
     ["Volume Gateway — cached", "iSCSI", "All data in S3, hot subset local"],
     ["Tape Gateway", "iSCSI VTL", "S3 and Glacier, looks like a tape library"]]),
  D([["Terabytes, and the line would take weeks?", "Snowball"],
     ["Petabytes?", "Snowmobile"],
     ["Ongoing sync, not a one-off move?", "DataSync"],
     ["On-premises apps must keep using a file share?", "File Gateway"],
     ["Backup software expects tapes?", "Tape Gateway"]]),
],
"Amazon EC2": [
  H("How you pay, and what you give up"),
  T(["Model", "Discount", "Commitment", "Interruptible?"],
    [["On-Demand", "—", "None", "No"],
     ["Reserved (1 or 3 yr)", "up to 72%", "Instance family and Region", "No"],
     ["Savings Plans", "up to 72%", "A dollar-per-hour spend", "No"],
     ["Spot", "up to 90%", "None", "Yes — two minutes' notice"],
     ["Dedicated Host", "—", "Per host", "No"]]),
  D([["Steady, always-on, known instance family?", "Reserved Instance / EC2 Instance Savings Plan"],
     ["Steady but you may change family or move to Fargate?", "Compute Savings Plan"],
     ["Interruption is genuinely fine?", "Spot"],
     ["Short, unpredictable, stateful?", "On-Demand"],
     ["Licence is bound to physical cores?", "Dedicated Host"]]),
  X("Spot is wrong for anything stateful the moment the question mentions sessions, a database, or “must not be interrupted”."),
],
"Security Groups": [
  T(["", "Security group", "Network ACL"],
    [["Operates on", "The instance (its ENI)", "The whole subnet"],
     ["Rules", "Allow only", "Allow and deny"],
     ["State", "Stateful — a reply is automatic", "Stateless — you must open the return path"],
     ["Evaluation", "All rules together", "In rule-number order, first match wins"],
     ["Default", "Denies inbound, allows outbound", "Default NACL allows everything"]]),
  X("Stateless is the whole trick. If a NACL lets traffic in on 443 but does not allow the ephemeral ports 1024–65535 back out, nothing works."),
],
"EC2 Placement Groups": [
  T(["Group", "Layout", "Use it for"],
    [["Cluster", "Packed into one rack, one AZ", "Lowest latency, highest throughput — HPC"],
     ["Spread", "Each instance on distinct hardware, up to 7 per AZ", "A handful of critical instances that must not share a fault"],
     ["Partition", "Groups of racks, partitions isolated", "HDFS, Cassandra, Kafka — rack awareness at scale"]]),
  X("Cluster placement lives in a single Availability Zone. If the question wants low latency AND survival of an AZ failure, cluster placement cannot give you both."),
],
"Elastic Block Store, EBS": [
  T(["Type", "Family", "Ceiling", "Reach for it when"],
    [["gp3", "SSD", "16,000 IOPS, 1,000 MB/s", "The sensible default; IOPS priced apart from size"],
     ["gp2", "SSD", "16,000 IOPS, tied to size", "Legacy; 3 IOPS per GiB"],
     ["io2 / io2 Block Express", "SSD", "64,000–256,000 IOPS", "Databases that need guaranteed IOPS, or Multi-Attach"],
     ["st1", "HDD", "500 MB/s", "Big sequential reads — logs, data warehouse"],
     ["sc1", "HDD", "250 MB/s", "Cold, rarely touched, cheapest"]]),
  K("EBS is tied to one Availability Zone. To move a volume, snapshot it — the snapshot goes to S3 and can be restored into any AZ or copied to another Region."),
  X("HDD types cannot be boot volumes. Neither can anything you attach to more than one instance unless it is io1/io2 with Multi-Attach."),
],
"EFS and FSx": [
  T(["Service", "Protocol", "Runs on", "Reach for it when"],
    [["EFS", "NFS", "Linux", "A shared POSIX file system across AZs, grows on its own"],
     ["FSx for Windows File Server", "SMB", "Windows", "Windows shares, AD integration, quotas"],
     ["FSx for Lustre", "Lustre", "Linux", "HPC and ML, sub-millisecond, links to S3"],
     ["FSx for NetApp ONTAP", "NFS + SMB + iSCSI", "Both", "One volume served to Linux and Windows at once"],
     ["FSx for OpenZFS", "NFS", "Linux", "Moving a ZFS workload across as-is"]]),
  D([["Many Linux instances, one share, must grow?", "EFS"],
     ["Windows and Active Directory?", "FSx for Windows"],
     ["Sub-millisecond over an S3 dataset?", "FSx for Lustre"],
     ["Both NFS and SMB on the same data?", "FSx for NetApp ONTAP"]]),
],
"Databases Overview": [
  T(["Need", "Service"],
    [["Relational, managed, familiar engine", "RDS"],
     ["Relational, cloud-native, 5× MySQL throughput", "Aurora"],
     ["Key-value, single-digit millisecond, serverless scale", "DynamoDB"],
     ["Petabyte analytics with SQL", "Redshift"],
     ["In-memory cache", "ElastiCache"],
     ["Graph", "Neptune"],
     ["Document / MongoDB API", "DocumentDB"],
     ["Ledger, immutable, cryptographically verifiable", "QLDB"],
     ["Time series", "Timestream"]]),
],
"RDS Specifics": [
  T(["", "Multi-AZ", "Read replica"],
    [["Purpose", "Availability", "Performance"],
     ["Replication", "Synchronous", "Asynchronous"],
     ["Can you read it?", "No — standby is idle", "Yes"],
     ["Failover", "Automatic, DNS swings over", "Manual promotion"],
     ["Same Region?", "Yes", "Same or another Region"]]),
  X("Multi-AZ is not a scaling feature and a read replica is not a high-availability feature. Questions mix the two on purpose."),
],
"DynamoDB": [
  T(["Choice", "Options", "Rule of thumb"],
    [["Capacity", "On-demand vs provisioned", "Unpredictable traffic → on-demand; steady → provisioned with auto scaling"],
     ["Reads", "Eventually vs strongly consistent", "Strongly consistent costs double and cannot be served by a replica"],
     ["Index", "LSI vs GSI", "LSI shares the partition key and must exist at table creation; GSI can be added later"],
     ["Table class", "Standard vs Standard-IA", "Standard-IA when storage dwarfs the request cost"]]),
  K("An item is capped at 400 KB. If a question mentions documents or blobs bigger than that, the answer stores them in S3 and keeps the pointer in DynamoDB."),
  K("DAX is a read cache and only a read cache — microsecond reads, no help at all for writes."),
],
"Aurora": [
  L(["Six copies of the data, spread over three Availability Zones.",
     "Tolerates losing two copies for writes, three for reads.",
     "Storage grows automatically, 10 GB at a time, to 128 TB.",
     "Up to 15 Aurora Replicas, failover in about 30 seconds.",
     "Global Database: cross-Region replication under a second, RPO measured in seconds."]),
  K("Aurora Serverless v2 scales capacity in place. Reach for it when the load is spiky or unknown, not when it is steady."),
],
"ElastiCache": [
  T(["", "Redis (OSS)", "Memcached"],
    [["Data structures", "Lists, sets, sorted sets, streams", "Strings only"],
     ["Persistence", "Yes", "No"],
     ["Replication / HA", "Yes, Multi-AZ with failover", "No"],
     ["Multi-threaded", "No", "Yes"],
     ["Reach for it when", "Leaderboards, sessions, anything that must survive", "A simple, horizontally scaled object cache"]]),
  X("“Must be highly available” or “must not lose the cache” rules Memcached out immediately."),
],
"Caching Strategies on AWS": [
  F(["User", "Route 53", "CloudFront", "API Gateway cache", "ElastiCache / DAX", "Database"],
    "Every layer you can answer from is a layer the database never sees."),
],
"Registering a Domain and Route 53 Routing Policies": [
  T(["Policy", "Decides by", "Classic use"],
    [["Simple", "Nothing — one record", "A single resource"],
     ["Weighted", "Percentages you set", "Canary release, A/B split"],
     ["Latency", "Measured latency to each Region", "Send users to the fastest Region"],
     ["Failover", "A health check", "Active-passive disaster recovery"],
     ["Geolocation", "Where the user is", "Language, licensing, legal boundaries"],
     ["Geoproximity", "Distance, with a bias you control", "Shifting traffic between Regions gradually"],
     ["Multivalue answer", "Up to 8 healthy records at random", "Cheap client-side load spreading"]]),
  K("An alias record points at an AWS resource, is free to query, and can sit at the zone apex. A CNAME cannot sit at the apex. That single fact answers a surprising number of questions."),
],
"NAT Instances and NAT Gateways": [
  T(["", "NAT instance", "NAT gateway"],
    [["You manage", "An EC2 instance you patch", "Nothing — managed"],
     ["Availability", "One instance; you build the failover", "Redundant inside one AZ"],
     ["Bandwidth", "Instance size", "Up to 100 Gbps"],
     ["Security group", "Yes", "No"],
     ["Bastion use", "Can double as one", "Cannot"]]),
  X("A NAT gateway is redundant within its Availability Zone, not across them. For a truly AZ-fault-tolerant design you need one per AZ and a route from each private subnet to its own."),
],
"Direct Connect": [
  T(["Virtual interface", "Reaches", "Typical use"],
    [["Private VIF", "One VPC, via a virtual private gateway", "Private IPs in a single VPC"],
     ["Public VIF", "AWS public endpoints — S3, DynamoDB", "Reaching public services without the internet"],
     ["Transit VIF", "A Direct Connect gateway plus transit gateways", "Many VPCs across Regions"]]),
  K("Direct Connect is not encrypted by itself. If a question demands encryption in transit, the answer is a VPN running over the Direct Connect link."),
],
"AWS Global Accelerator and VPC Endpoints": [
  T(["", "Gateway endpoint", "Interface endpoint (PrivateLink)"],
    [["Services", "S3 and DynamoDB only", "Almost everything else"],
     ["How it works", "A route-table entry", "An ENI with a private IP"],
     ["Cost", "Free", "Per hour and per GB"],
     ["Reachable from on-premises", "No", "Yes, over DX or VPN"]]),
  X("A gateway endpoint cannot be reached from on-premises and does not carry IPv6. Both facts turn up as the deciding detail."),
],
"Load Balancers": [
  T(["", "Application LB", "Network LB", "Gateway LB"],
    [["Layer", "7 — HTTP/HTTPS", "4 — TCP/UDP/TLS", "3 — IP"],
     ["Routes on", "Path, host, header, query", "Protocol and port", "All traffic, to appliances"],
     ["Static IP", "No (use Global Accelerator)", "Yes, one per AZ", "—"],
     ["Speed", "Fast", "Millions of requests/sec, ultra-low latency", "—"],
     ["Reach for it when", "A web app or microservices", "Extreme performance, a static IP, non-HTTP", "Firewalls and IDS/IPS in the path"]]),
  X("A WAF web ACL attaches to an ALB, CloudFront, API Gateway or AppSync — never to an NLB. If the question needs WAF, the answer needs a layer-7 entry point."),
],
"Auto Scaling": [
  T(["Policy", "Reacts to", "Reach for it when"],
    [["Target tracking", "A metric held at a target", "The normal answer — keep CPU at 50%"],
     ["Step scaling", "Alarm thresholds, in steps", "Different sized responses to different breaches"],
     ["Simple scaling", "One alarm, then a cooldown", "Legacy; the cooldown makes it sluggish"],
     ["Scheduled", "The clock", "A known pattern — every weekday at 8am"],
     ["Predictive", "A learned daily/weekly pattern", "Recurring load, warms up before the spike"]]),
  K("Scaling on SQS queue depth, using ApproximateNumberOfMessagesVisible as a custom metric, is the standard answer for a worker fleet."),
],
"Amazon SQS": [
  T(["", "Standard queue", "FIFO queue"],
    [["Order", "Best effort", "Strictly preserved"],
     ["Delivery", "At least once — duplicates possible", "Exactly once"],
     ["Throughput", "Nearly unlimited", "300 msg/s, 3,000 batched"],
     ["Name", "Anything", "Must end in .fifo"]]),
  K("Visibility timeout is the reason for duplicate processing: if the worker has not deleted the message by the time it expires, the message comes back and someone else picks it up."),
  X("S3 event notifications cannot target a FIFO queue directly. Route the event through EventBridge when a question needs both S3 events and exactly-once ordering."),
],
"Amazon SNS": [
  F(["Publisher", "SNS topic", "SQS queue / Lambda / HTTP endpoint"],
    "Fan-out: one message, many independent subscribers, each with its own filter policy."),
  T(["", "SNS", "SQS", "Kinesis Data Streams", "EventBridge"],
    [["Model", "Push, pub/sub", "Pull, queue", "Ordered stream", "Event bus with rules"],
     ["Consumers", "Many at once", "One per message", "Many, each at its own position", "Many, matched by pattern"],
     ["Replay", "No", "No", "Yes, within retention", "Archive and replay"]]),
],
"Amazon Kinesis": [
  T(["Service", "It does", "Reach for it when"],
    [["Data Streams", "Ordered, replayable stream you manage", "Custom processing, multiple consumers, replay"],
     ["Data Firehose", "Load to S3, Redshift, OpenSearch", "Just get it into a store, near real time, no code"],
     ["Managed Service for Apache Flink", "SQL / Flink over the stream", "Aggregating or transforming in flight"],
     ["Video Streams", "Ingest video", "Cameras and media"]]),
  K("Firehose is near real time — a buffer measured in seconds — and it cannot replay. If the question says replay or sub-second, it means Data Streams."),
],
"Security: KMS": [
  T(["", "KMS", "CloudHSM"],
    [["Tenancy", "Shared, managed by AWS", "A single-tenant hardware module"],
     ["Key control", "AWS manages the hardware; you hold the policy", "You alone — AWS cannot recover it"],
     ["FIPS level", "140-2 level 3 validated HSMs", "140-2 level 3, dedicated"],
     ["Reach for it when", "Nearly everything", "A regulator insists on single tenancy, or you need PKCS#11"]]),
  K("Envelope encryption: KMS encrypts a data key, the data key encrypts the data. It is why a 5 TB object can be protected by a key that never leaves KMS."),
  X("An S3 Bucket Key cuts KMS API calls — and therefore cost — by up to 99%. “Too many KMS requests” has exactly one intended answer."),
],
"Systems Manager Parameter Store and Secrets Manager": [
  T(["", "Parameter Store", "Secrets Manager"],
    [["Cost", "Free (standard tier)", "Per secret, per month"],
     ["Rotation", "You build it", "Built in, managed for RDS and others"],
     ["Size", "4 KB standard, 8 KB advanced", "64 KB"],
     ["Cross-account", "No", "Yes"]]),
  K("If the question says “rotate automatically” and does not say “cheapest”, it is Secrets Manager."),
],
"AWS Shield": [
  T(["", "Shield Standard", "Shield Advanced"],
    [["Cost", "Free, always on", "$3,000/month"],
     ["Protects against", "Common layer 3/4 attacks", "Large and sophisticated attacks, layer 7"],
     ["Support", "None", "24/7 DDoS Response Team"],
     ["Cost protection", "No", "Refunds scaling charges caused by an attack"]]),
],
"Serverless: AWS Lambda": [
  L(["Maximum run time 15 minutes — the single most useful fact in the exam.",
     "Memory from 128 MB to 10,240 MB; CPU scales with memory.",
     "Ephemeral /tmp from 512 MB to 10,240 MB.",
     "Deployment package 50 MB zipped, 250 MB unzipped, or 10 GB as a container image."]),
  T(["Concurrency setting", "What it does"],
    [["Reserved", "Caps the function and guarantees it that slice of the account limit"],
     ["Provisioned", "Keeps instances warm — the cure for cold starts, and it costs money"],
     ["SnapStart", "Snapshots an initialised Java function and restores it, cheaper than provisioned"]]),
  X("A job that takes more than 15 minutes is never Lambda. Fargate or Batch is the answer."),
],
"ECS": [
  T(["", "ECS on EC2", "ECS on Fargate", "EKS"],
    [["You manage", "The instances", "Nothing", "Nodes, unless Fargate"],
     ["Pricing", "Per instance", "Per vCPU and GB used", "Per cluster plus compute"],
     ["Reach for it when", "You need control, GPUs, or cheap Spot capacity", "You want containers with no servers", "You already run Kubernetes"]]),
  K("Task role = permissions for the container's own API calls. Task execution role = permissions ECS needs to pull the image and write logs. Questions swap them deliberately."),
],
"CloudWatch and CloudTrail": [
  T(["", "CloudWatch", "CloudTrail", "AWS Config"],
    [["Answers", "How is it performing?", "Who did what, and when?", "Is it configured as it should be?"],
     ["Data", "Metrics, logs, alarms", "API call history", "Configuration state over time"],
     ["Classic use", "Alarm on CPU or a log pattern", "Auditing a deletion", "Detecting an unencrypted volume"]]),
  X("Memory and disk usage are not standard EC2 metrics. They need the CloudWatch agent — a favourite distractor."),
],
"On-Premises Migration Strategies with AWS": [
  T(["Strategy", "Means"],
    [["Rehost", "Lift and shift, unchanged"],
     ["Replatform", "Lift and reshape — move the DB to RDS"],
     ["Repurchase", "Drop it and buy SaaS"],
     ["Refactor", "Rewrite it cloud-native"],
     ["Retire", "Turn it off"],
     ["Retain", "Leave it where it is, for now"]]),
  F(["Discover — Application Discovery Service", "Plan — Migration Hub", "Move — MGN / DMS / DataSync", "Verify"]),
],
}

# ------------------------------------------------------- comprehension checks
# Three per chapter, written from the notes above them. Deliberately easy: they
# check that the page was read, they are not exam-difficulty questions.
QUIZ = {
0: [
  ("Your users are in one country whose law says their data must stay inside its borders. Which factor decides your Region?",
   ["Compliance", "Latency", "Price", "Service availability"], 0),
  ("What connects the Availability Zones inside one Region?",
   ["Fast, resilient, low-latency fibre", "The public internet", "A VPN you configure", "Direct Connect"], 0),
  ("Who patches the guest operating system on an EC2 instance you launched?",
   ["You do", "AWS does", "Nobody — it is immutable", "The Marketplace vendor"], 0),
],
1: [
  ("A new IAM user is created with no policies attached. What can they do?",
   ["Nothing", "Read every service", "Everything the root user can", "Only billing"], 0),
  ("An application on EC2 needs to read an S3 bucket. What is the correct mechanism?",
   ["An IAM role attached to the instance", "An access key in the user data script",
    "The root account's keys", "A bucket ACL naming the instance ID"], 0),
  ("An SCP denies an action, and the account's IAM policy allows it. What happens?",
   ["The action is denied", "The action is allowed", "It depends on the order",
    "Only the root user can do it"], 0),
],
2: [
  ("Data is read infrequently but must come back in milliseconds when it is read, and losing it would be serious. Which class?",
   ["S3 Standard-Infrequent Access", "S3 One Zone-IA", "Glacier Deep Archive", "Glacier Flexible Retrieval"], 0),
  ("The company must be able to prove who used the encryption key and when. Which option?",
   ["SSE-KMS", "SSE-S3", "SSE-C", "No encryption is needed"], 0),
  ("You turn on Cross-Region Replication. What happens to the objects already in the bucket?",
   ["Nothing — only new objects replicate", "They all replicate immediately",
    "They replicate after 30 days", "They are deleted from the source"], 0),
],
3: [
  ("A batch job runs for three hours, can be restarted, and cost matters most. Which purchasing option?",
   ["Spot Instances", "On-Demand", "Dedicated Hosts", "Reserved Instances"], 0),
  ("Which placement group packs instances together for the lowest possible network latency?",
   ["Cluster", "Spread", "Partition", "Dedicated"], 0),
  ("A security group allows inbound 443. Does the reply need an outbound rule?",
   ["No — security groups are stateful", "Yes, on port 443", "Yes, on the ephemeral ports",
    "Only if a NACL exists"], 0),
],
4: [
  ("You need one file system mounted by many Linux instances across several Availability Zones. What do you use?",
   ["Amazon EFS", "An EBS volume", "Instance store", "FSx for Windows File Server"], 0),
  ("An EBS volume is in us-east-1a and you need the data in us-east-1b. What do you do?",
   ["Snapshot it and restore the snapshot into the other AZ", "Drag it across in the console",
    "Attach it to an instance in the other AZ", "Enable Multi-AZ on the volume"], 0),
  ("Which workload points at FSx for Lustre?",
   ["HPC and machine learning over data in S3", "A Windows department file share",
    "An ordinary web server's root disk", "A relational database"], 0),
],
5: [
  ("Which RDS feature exists for availability rather than performance?",
   ["Multi-AZ", "Read replicas", "Performance Insights", "Parameter groups"], 0),
  ("An item in DynamoDB must hold a 3 MB document. What is the design?",
   ["Put the document in S3 and store the pointer in DynamoDB", "Split it over four items",
    "Enable DAX", "Switch the table class to Standard-IA"], 0),
  ("The cache must survive a node failure and hold sorted sets. Which engine?",
   ["Redis", "Memcached", "Either — they are the same", "Neither; use DynamoDB"], 0),
],
6: [
  ("Which record type can sit at the zone apex and costs nothing to query?",
   ["An alias record", "A CNAME record", "An MX record", "A TXT record"], 0),
  ("You want users sent to whichever Region answers fastest for them. Which routing policy?",
   ["Latency", "Geolocation", "Weighted", "Simple"], 0),
  ("Which routing policy is the one built around a health check for active-passive DR?",
   ["Failover", "Multivalue answer", "Geoproximity", "Weighted"], 0),
],
7: [
  ("Instances in a private subnet must download patches but must not be reachable from the internet. What do you add?",
   ["A NAT gateway in a public subnet", "An internet gateway on the private subnet",
    "A public IP on each instance", "A VPC peering connection"], 0),
  ("Which of these is stateless and therefore needs an explicit rule for return traffic?",
   ["A network ACL", "A security group", "An internet gateway", "A route table"], 0),
  ("Which endpoint type is free and works only for S3 and DynamoDB?",
   ["A gateway endpoint", "An interface endpoint", "A PrivateLink service", "A transit gateway"], 0),
],
8: [
  ("Traffic must be routed by URL path to different target groups. Which load balancer?",
   ["Application Load Balancer", "Network Load Balancer", "Gateway Load Balancer", "Classic Load Balancer"], 0),
  ("You need a static IP address per Availability Zone and extreme throughput. Which load balancer?",
   ["Network Load Balancer", "Application Load Balancer", "Gateway Load Balancer", "None can do this"], 0),
  ("A worker fleet should grow with the backlog. Which metric do you scale on?",
   ["The SQS queue depth", "The load balancer's latency", "Instance memory", "The number of AZs"], 0),
],
9: [
  ("Orders must be processed in the order they arrive, exactly once. Which queue?",
   ["An SQS FIFO queue", "An SQS standard queue", "An SNS topic", "A Kinesis video stream"], 0),
  ("One event must reach four independent consumers at the same time. What do you use?",
   ["An SNS topic with four subscribers", "One SQS queue read four times",
    "Four Lambda functions polling S3", "A Kinesis Firehose stream"], 0),
  ("The team needs to replay the last 24 hours of events. Which service supports that?",
   ["Kinesis Data Streams", "Amazon SNS", "Kinesis Data Firehose", "An SQS standard queue"], 0),
],
10: [
  ("Which service gives you a single-tenant hardware security module that AWS cannot recover for you?",
   ["CloudHSM", "KMS", "Secrets Manager", "Parameter Store"], 0),
  ("KMS charges are high because of the number of requests from S3. What fixes it?",
   ["Turn on an S3 Bucket Key", "Switch to SSE-C", "Disable encryption", "Move to Glacier"], 0),
  ("A database password must rotate every 30 days with no code to maintain. Which service?",
   ["Secrets Manager", "Parameter Store", "KMS", "IAM"], 0),
],
11: [
  ("A job reliably takes 25 minutes. Can Lambda run it?",
   ["No — Lambda stops at 15 minutes", "Yes, with more memory",
    "Yes, with provisioned concurrency", "Yes, if it is a container image"], 0),
  ("Which setting removes cold-start latency by keeping instances initialised?",
   ["Provisioned concurrency", "Reserved concurrency", "A larger deployment package", "A VPC attachment"], 0),
  ("You want containers with no servers to manage at all. Which launch type?",
   ["Fargate", "EC2", "Self-managed Kubernetes on EC2", "Outposts"], 0),
],
12: [
  ("Who deleted that bucket, and when? Which service answers it?",
   ["CloudTrail", "CloudWatch", "AWS Config", "Trusted Advisor"], 0),
  ("You need an alarm when an EC2 instance's memory usage is high. What is required?",
   ["The CloudWatch agent — memory is not a default metric", "Nothing, it is a default metric",
    "AWS Config", "A VPC flow log"], 0),
  ("Moving a database to RDS as part of a migration, without rewriting the application, is called what?",
   ["Replatform", "Rehost", "Refactor", "Repurchase"], 0),
],
}


def paragraphs(body):
    out = []
    for para in [p.strip() for p in body.split("\n\n")]:
        if para:
            out.append({"t": "p", "x": para})
    return out


def main():
    raw = SRC.read_text(encoding="utf-8")
    parts = re.split(r"^## ", raw, flags=re.M)[1:]
    topics = []
    for part in parts:
        title, _, body = part.partition("\n")
        title = title.strip()
        blocks = paragraphs(body)
        blocks += EXTRAS.get(title, [])
        topics.append({"nm": title, "blocks": blocks})

    seen = {t["nm"] for t in topics}
    missing = seen - set(SECTION_CH)
    assert not missing, "no chapter for: %s" % sorted(missing)
    stale = set(SECTION_CH) - seen
    assert not stale, "chapter mapping names a topic that is gone: %s" % sorted(stale)

    chapters = []
    for i, (nm, em, sub) in enumerate(CHAPTERS):
        mine = [t for t in topics if SECTION_CH[t["nm"]] == i]
        assert mine, "chapter %s has no topics" % nm
        quiz = []
        for q, opts, ans in QUIZ.get(i, []):
            assert 0 <= ans < len(opts), q
            assert len(set(opts)) == len(opts), "repeated option: " + q
            quiz.append({"q": q, "o": opts, "a": ans})
        assert len(quiz) >= 3, "chapter %s needs at least three checks" % nm
        words = sum(len(b.get("x", "").split()) if isinstance(b.get("x"), str) else 40
                    for t in mine for b in t["blocks"])
        chapters.append({"nm": nm, "em": em, "sub": sub, "min": max(2, round(words / 200)),
                         "topics": mine, "quiz": quiz})

    # nothing empty, nothing malformed
    for c in chapters:
        for t in c["topics"]:
            assert t["blocks"], "%s / %s has no content" % (c["nm"], t["nm"])
            for b in t["blocks"]:
                assert b["t"] in {"h", "p", "list", "steps", "table", "flow", "split",
                                  "key", "trap", "note", "code", "dtree"}, b["t"]
                if b["t"] == "table":
                    assert b["head"] and b["rows"], t["nm"]
                    for r in b["rows"]:
                        assert len(r) == len(b["head"]), "%s: ragged table row %r" % (t["nm"], r)

    data = {"v": 1, "chapters": chapters}
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    page = PAGE.read_text(encoding="utf-8")
    pat = re.compile(r'(<script id="studydata" type="application/json">).*?(</script>)', re.S)
    if pat.search(page):
        page = pat.sub(lambda m: m.group(1) + blob + m.group(2), page, count=1)
    else:
        anchor = '<script id="data" type="application/json">'
        assert anchor in page, "#data not found"
        page = page.replace(anchor,
                            '<script id="studydata" type="application/json">' + blob + '</script>\n' + anchor, 1)
    PAGE.write_text(page, encoding="utf-8")

    tt = sum(len(c["topics"]) for c in chapters)
    tb = sum(len(t["blocks"]) for c in chapters for t in c["topics"])
    extras = sum(1 for c in chapters for t in c["topics"] for b in t["blocks"]
                 if b["t"] not in ("p",))
    print(f"{len(chapters)} chapters, {tt} topics, {tb} blocks "
          f"({extras} tables/flows/callouts authored), "
          f"{sum(len(c['quiz']) for c in chapters)} checks")
    for c in chapters:
        print(f"   {c['em']} {c['nm']:<26} {len(c['topics']):2d} topics · {c['min']:2d} min")


if __name__ == "__main__":
    sys.exit(main())

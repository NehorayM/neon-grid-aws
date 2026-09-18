# -*- coding: utf-8 -*-
"""Reviewed answer key for the exam-dump questions.

Every question in questions_clean.json gets an entry here. The value is the answer I
determined by reading the question, independently of what the CSV claimed. NOTES records
why an entry differs from the CSV, or why a close call went the way it did, so the
decision can be checked rather than taken on trust.
"""
V = {}
NOTES = {}

V.update({
 7:"C", 8:"C", 9:"C", 10:"D", 11:"A", 12:"C", 13:"D", 14:"D", 15:"A", 16:"B",
 17:"A", 18:"D", 19:"CD", 20:"C", 21:"A", 22:"A", 23:"B", 24:"B", 25:"D", 26:"D",
 27:"B", 28:"A",
})
NOTES.update({
 14:"gp3 tops out at 16,000 IOPS, so raising gp3 IOPS cannot reach the 20,000 the workload needs; io2 can.",
 23:"An Auto Scaling group cannot span Regions, which is what rules out the otherwise similar option A.",
})

V.update({
 29:"D", 30:"BC", 31:"A", 32:"D", 33:"B", 34:"B", 35:"C", 36:"AC", 37:"D", 38:"D",
 39:"C", 40:"D", 41:"A", 42:"C", 43:"A", 44:"A", 45:"C", 46:"B", 47:"B", 48:"D",
 49:"C", 50:"A",
})
NOTES.update({
 40:"Each model loads 1 GB at start-up and usage is irregular, so Lambda would pay that cost on every cold start; ECS behind a queue holds the model in memory.",
 47:"Changed from the file's A. The stem sets no retrieval-time requirement and the files are never read after a month, so Deep Archive is roughly ten times cheaper than Standard-IA and is the most cost-effective transition.",
 48:"WAF attaches to an API Gateway REST API directly, so putting CloudFront in front of it only to host WAF is extra work.",
})

V.update({
 51:"D", 52:"B", 53:"D", 54:"AE", 55:"A", 56:"A", 57:"C", 58:"B", 59:"A", 60:"AB",
 61:"A", 62:"D", 63:"B", 64:"B", 65:"A", 66:"D", 67:"A", 68:"A", 69:"B", 70:"B",
 71:"A", 72:"B",
})
NOTES.update({
 60:"WAF cannot attach to a Network Load Balancer, which is what rules out option D.",
 64:"Access to the underlying operating system is what selects RDS Custom over plain RDS for Oracle.",
 68:"Option C grants read only; the application also writes to the tables.",
})

V.update({
 73:"A", 74:"AE", 75:"B", 76:"D", 77:"B", 78:"B", 79:"B", 80:"D", 81:"C", 82:"A",
 83:"C", 84:"A", 85:"A", 86:"A", 87:"C", 88:"C", 89:"A", 90:"D", 91:"B", 92:"D",
 93:"D", 94:"C", 95:"B", 96:"B", 97:"DE", 98:"B", 99:"D", 100:"A", 101:"A", 102:"D",
})
NOTES.update({
 87:"DNS validation is what allows ACM to renew without human action; email validation needs someone to click a link each time.",
 93:"Changed from the file's A. AWS Config has no rule that sees the Organizations OU hierarchy; Control Tower's own drift detection reports an account moved between OUs and publishes it to SNS.",
})

V.update({
 103:"D", 104:"D", 106:"A", 107:"C", 108:"D", 109:"C", 110:"A", 111:"B", 112:"AC", 113:"B",
 114:"B", 115:"B", 116:"D", 117:"C", 118:"A", 119:"D", 120:"C", 121:"A", 122:"D", 123:"D",
 124:"D", 125:"D", 126:"C", 127:"D", 128:"D", 129:"A", 130:"AC", 131:"A", 132:"D", 133:"A",
})
NOTES.update({
 107:"Compliance mode is what makes the retention unalterable; governance mode can be overridden by a privileged user.",
 113:"Two instances must always be running, so each Availability Zone needs two: losing a zone still leaves two.",
 118:"Kept the file's A. Glacier Flexible Retrieval at day 30 would be cheaper per GB but carries a 90-day minimum charge, and the guidance for data that may still be analysed is Standard-IA.",
 121:"EBS Multi-Attach is supported on io1 and io2 only.",
 130:"Kept the file's A and C. The 30-minute job exceeds a single Lambda invocation, so this relies on Step Functions splitting it into steps; Fargate would also serve.",
 132:"A certificate for a Regional API Gateway endpoint must be in the same Region, unlike CloudFront which requires us-east-1.",
})

V.update({
 134:"D", 135:"C", 136:"A", 137:"B", 138:"D", 139:"B", 140:"A", 141:"D", 142:"C", 143:"C",
 144:"BC", 145:"CE", 146:"B", 147:"C", 148:"AC", 149:"D", 150:"CE", 151:"A", 152:"A", 153:"C",
 154:"B", 155:"C", 156:"DE", 157:"A", 158:"A", 159:"BE", 160:"B", 161:"C", 162:"C", 163:"B",
})
NOTES.update({
 139:"UDP rules out an Application Load Balancer, and global reach rules out a single-Region load balancer on its own.",
 155:"Only a Capacity Reservation guarantees capacity exists in the failover Region; Savings Plans and Reserved Instances are billing constructs.",
 163:"Scratch file systems are not replicated, so the highly available requirement selects persistent.",
})

V.update({
 164:"C", 165:"A", 166:"A", 167:"D", 168:"A", 169:"B", 170:"AB", 171:"A", 172:"C", 173:"CE",
 174:"B", 175:"D", 176:"B", 177:"A", 178:"B", 179:"B", 180:"D", 181:"D", 182:"D", 183:"C",
 184:"B", 185:"AB", 186:"A", 187:"A", 188:"A", 189:"B", 190:"A", 191:"D", 192:"A", 193:"B",
})
NOTES.update({
 167:"AD Connector is what reaches an on-premises directory without replicating it, which is why D is more complete than A.",
 176:"Jobs run up to 20 minutes, which is beyond a Lambda invocation, so the scheduled target has to be a Fargate task.",
 186:"Changed from the file's B. B has every account owner sharing one mailbox, which is the least secure option here; a distribution list per account with per-team alternate contacts is the practice AWS documents.",
 189:"Changed from the file's C. SageMaker Pipelines is not a valid S3 event notification destination - only SNS, SQS, Lambda and EventBridge are - so the rule has to go through EventBridge, and managed replication beats a copy function for overhead.",
 192:"Changed from the file's D. Read replicas do not fail over automatically, so they do not meet 'must recover automatically'; a Multi-AZ DB cluster gives automatic failover and a reader endpoint for the analytical queries.",
})

V.update({
 194:"D", 195:"B", 196:"B", 197:"A", 198:"D", 199:"D", 200:"A", 201:"A", 202:"AE", 203:"D",
 204:"C", 205:"C", 206:"BD", 207:"B", 208:"D", 209:"C", 210:"A", 211:"D", 212:"A", 213:"B",
 214:"B", 215:"D", 216:"C", 217:"BE", 218:"D", 219:"B", 220:"B", 221:"C", 222:"A", 223:"AD",
})
NOTES.update({
 199:"Kept the file's D. A Systems Manager State Manager association using the built-in start and stop runbooks would need no code and is arguably lighter, but both meet the requirement.",
 200:"A gateway endpoint carries no hourly charge; an interface endpoint does, which is what 'most cost-effectively' turns on.",
 208:"Changed from the file's B. The files are rarely read after 30 days and must stay immediately accessible, which is exactly Glacier Instant Retrieval; it is roughly a third the price of Standard-IA and the four-year life clears its 90-day minimum.",
 215:"Only client-side encryption keeps plaintext away from anyone handling the data before it reaches S3.",
 217:"Changed from the file's A,B. A Compute Savings Plan covers EC2, Lambda and Fargate but not SageMaker, so option A is wrong on its face; SageMaker needs its own plan.",
})

V.update({
 225:"C", 226:"A", 227:"A", 228:"D", 229:"CE", 230:"B", 231:"B", 232:"A", 233:"B", 234:"D",
 235:"C", 236:"C", 237:"B", 238:"A", 239:"C", 240:"C", 241:"D", 242:"A", 243:"B", 244:"C",
 245:"A", 246:"D", 247:"D", 248:"B", 249:"A", 250:"A", 251:"A", 252:"A", 253:"D", 254:"A",
})
NOTES.update({
 226:"Compliance mode for 100 years would stop the company modifying the objects when it chooses, which the stem allows; a legal hold can be lifted by named users.",
 234:"Changed from the file's C. The existing job regularly runs longer than 30 minutes, which a Lambda function cannot do; an EMR Serverless job driven by Step Functions has no such ceiling.",
 238:"Option A's text had the two services reversed in transcription, which inverted the question; it is repaired to the mapping the stem asks for, and IRSA remains the mechanism.",
 250:"A custom endpoint targets a chosen subset of replicas; the reader endpoint would spread across all six.",
 253:"Changed from the file's C. RDS has no 'on-demand capacity mode' and does not scale with traffic on its own, which the stem requires; Aurora Serverless does and still provides automated backups.",
})

V.update({
 255:"D", 256:"C", 257:"C", 258:"A", 259:"B", 260:"A", 261:"C", 262:"A", 263:"D", 264:"B",
 265:"B", 266:"D", 267:"D", 268:"CE", 269:"AD", 270:"C", 271:"C", 272:"A", 273:"C", 274:"C",
 275:"D", 276:"A", 277:"D", 278:"D", 279:"D", 280:"AD", 281:"D", 282:"AC", 283:"C", 284:"C",
})
NOTES.update({
 255:"Changed from the file's C. RDS automated backup retention caps at 35 days, so it cannot hold 90 days; an AWS Backup plan can, and it also provides point-in-time restore.",
 258:"Changed from the file's D. The Glue DynamoDB export connector reads a table export in S3 and consumes no read capacity, which is the stated constraint; the Athena connector scans the table and does consume it.",
 262:"Changed from the file's D. The stem asks for block storage across Availability Zones: FSx for Windows File Server serves SMB file shares, while FSx for NetApp ONTAP Multi-AZ presents iSCSI block devices.",
 268:"Changed from the file's D,E. D and E describe two different designs - if an SQS queue buffers the messages, no Lambda resource policy for SNS is needed. The coherent pair is the topic policy allowing the cross-account subscription plus the Lambda resource policy.",
 269:"Changed from the file's A,B. The automation document registers and deregisters targets by instance ID, which is why it errors against an IP address target group; maintenance windows only schedule the work.",
 271:"Steady state must stay up, so it runs on Fargate; the short bursts are what can tolerate Spot interruption.",
})

V.update({
 285:"AC", 286:"C", 287:"D", 288:"B", 289:"B", 290:"C", 291:"D", 292:"D", 293:"A", 294:"AD",
 295:"A", 296:"B", 297:"B", 298:"D", 299:"D", 300:"A", 301:"A", 302:"A", 303:"C", 304:"C",
 305:"B", 306:"A", 307:"B", 308:"D", 309:"A", 310:"C", 311:"A", 312:"B", 313:"C", 314:"B",
})
NOTES.update({
 285:"Changed from the file's C,D. The instances run Windows Server, and EFS is an NFS file system that Windows cannot mount; FSx for Windows File Server is the shared storage for them.",
 296:"Core nodes hold HDFS data, so losing one loses data; only the task nodes can safely run on Spot.",
 304:"Data Quality Services is not available on RDS for SQL Server, which is why all three tiers stay on EC2.",
})

V.update({
 315:"C", 316:"D", 317:"B", 319:"DE", 320:"D", 321:"D", 322:"B", 323:"B", 324:"A", 325:"A",
 326:"BE", 327:"BD", 328:"B", 329:"CE", 330:"B", 331:"C", 332:"A", 333:"B", 334:"D", 335:"D",
 336:"C", 337:"D", 338:"B", 339:"A", 340:"A", 341:"C", 342:"C", 343:"AE", 344:"AE", 345:"D",
 346:"B", 347:"B", 348:"C", 349:"B", 350:"D", 351:"AD", 352:"A", 353:"A", 354:"A", 355:"C",
 356:"D", 357:"C", 358:"C", 359:"B", 360:"C",
})
NOTES.update({
 315:"Changed from the file's B. Secrets Manager rotates on a schedule as a managed feature, while the Parameter Store option still requires a rotation Lambda to be written and maintained.",
 320:"At-least-once delivery is a standard queue; a FIFO queue is exactly-once, and the stem only asks for at least once, which makes the cheaper standard queue correct.",
 325:"Changed from the file's B. The stem forbids training a model, and SageMaker Autopilot trains one; Rekognition's moderation is pre-trained, and the content is photos rather than video.",
 326:"Changed from the file's D,E. Replacing the instance with a larger one is vertical scaling and provides no availability; the load balancer is what pairs with the Auto Scaling group.",
 327:"Changed from the file's B,E. Tag policies govern which tag values are allowed; they cannot deny RunInstances or deny untagging. Preventing those actions requires service control policies.",
 335:"Changed from the file's A. Textract only extracts text; sentiment needs Comprehend, which QuickSight cannot provide.",
 337:"Changed from the file's A. A security group cannot create a network path from the office to a private subnet - something has to carry the traffic, which is what the Site-to-Site VPN does.",
 338:"Changed from the file's A. CloudTrail records API calls, not inter-service latency; Container Insights plus X-Ray is the observability pairing for microservices.",
 340:"Changed from the file's B. Rotation of an AWS managed key is fixed and cannot be controlled, and the stem requires control over rotation, which only a customer managed key gives.",
 357:"Kept the file's C. An AWS managed key would cost less, but a customer managed key is the one whose rotation you configure and audit explicitly.",
 359:"Kept the file's B, though AWS has since retired Scheduled Reserved Instances; Spot is ruled out because the workload cannot tolerate interruption.",
})

V.update({
 361:"A", 362:"C", 363:"C", 364:"BC", 365:"B", 366:"B", 367:"D", 368:"ACD", 369:"B", 370:"D",
 371:"A", 372:"A", 373:"A", 374:"B", 375:"BE", 376:"C", 377:"B", 378:"B", 379:"BDF", 380:"D",
 381:"C", 382:"A", 383:"B", 384:"A", 385:"C", 386:"C", 387:"B", 388:"B", 389:"A", 390:"D",
 391:"A", 392:"A", 393:"B", 394:"BCD", 395:"C", 396:"D", 397:"D", 398:"A", 399:"A", 400:"A",
 401:"D", 402:"B", 403:"C", 404:"C", 405:"AD",
})
NOTES.update({
 368:"Changed from the file's A,C,E. The Schema Conversion Tool inspects database schemas, not virtual machines; the third step of a rehost is stopping the source and launching the cutover instance.",
 374:"Redis persists to disk, which is what the restart requirement asks for; Memcached does not.",
 376:"Changed from the file's D. The company already runs IAM Identity Center, so permission sets assigned to groups are the native and lightest mechanism; hand-managed IAM roles per team is more work.",
 383:"Changed from the file's D. Denying deletion outright would keep every snapshot forever, which the stem rules out; a Recycle Bin retention rule restores accidentally deleted snapshots for seven days.",
 393:"Geoproximity routes by distance between user and resource, which is what 'closest to the user' asks for; geolocation maps a country or continent to a chosen endpoint.",
 398:"Changed from the file's C. 64,000 IOPS is the io1 maximum, so it cannot be raised further; striping several volumes with LVM is how the instance gets past a single volume's ceiling.",
 399:"Network Load Balancers only support a security group if one is attached at creation, which is why the answer recreates it.",
 400:"Changed from the file's D. Express workflows are at-least-once and do not support the callback pattern a human approval step needs; the stem requires exactly once.",
})

V.update({
 406:"D", 407:"BD", 408:"A", 409:"CD", 410:"C", 411:"D", 412:"AC", 413:"A", 414:"AB", 415:"A",
 416:"AB", 417:"C", 418:"A", 419:"B", 420:"AD", 421:"A", 422:"B", 423:"A", 424:"D", 425:"C",
 426:"B", 427:"D", 428:"D", 429:"C", 430:"BCE", 431:"D", 432:"A", 434:"B", 435:"D", 436:"B",
 437:"C", 438:"B", 439:"C", 440:"D", 441:"B", 442:"A", 443:"C", 444:"D", 445:"A", 446:"C",
 447:"B", 448:"B", 449:"D", 450:"B",
})
NOTES.update({
 407:"Changed from the file's B,C. Vertical scaling does nothing for availability, which the stem also asks for; the launch template built from an AMI is what the Auto Scaling group needs.",
 415:"Changed from the file's C. Thousands of servers pull the same 100 files, so edge caching is the win; Transfer Acceleration optimises the path to the bucket but caches nothing.",
 419:"Changed from the file's A. Glacier classes bill a 128 KB minimum per object, so 10 KB files must be grouped first, and Deep Archive is the cheaper home for a seven-year archive.",
 420:"Changed from the file's A,E. Parameter Store has no built-in rotation, which the stem requires; the Lambda layer is how thousands of functions retrieve the secret without each one calling the API directly.",
 429:"VPN CloudHub is the hub-and-spoke design for several offices over VPN and costs less than a transit gateway for this.",
 430:"Changed from the file's D,E,F. Version IDs survive replication but not a copy, so batch replication is required; a hand-written CopyObject script is the opposite of least overhead.",
 436:"Queries are rarely repeated and the data changes constantly, which is what rules a cache out and leaves the read replica.",
 441:"Changed from the file's A. An EFS replication destination is read-only, so users could not upload in both Regions; DataSync tasks in opposite directions give the two-way movement the stem asks for.",
 443:"API Gateway caps a request payload at 10 MB, so a 12 MB upload has to go straight to S3 with a presigned URL.",
})

V.update({
 452:"B", 453:"C", 454:"A", 455:"A", 456:"B", 457:"B", 458:"D", 459:"D", 460:"B", 461:"C",
 462:"D", 463:"ACE", 464:"D", 465:"A", 466:"A", 467:"A", 468:"B", 469:"B", 470:"C", 471:"D",
 472:"B", 473:"A", 474:"C", 475:"C", 476:"C", 477:"B", 478:"A", 479:"C", 480:"A", 481:"C",
 482:"AE", 483:"C", 484:"C", 485:"C", 486:"D", 487:"A", 488:"A", 489:"D", 490:"D", 491:"D",
 492:"D", 493:"A", 494:"D", 495:"A", 496:"D",
})
NOTES.update({
 454:"Changed from the file's B. The cache must persist, and Memcached does not; Redis does. A database also cannot be a CloudFront origin.",
 465:"Changed from the file's B. AWS Budgets has a native action that stops instances, so routing through SNS and a Lambda function is extra machinery for the same result.",
 470:"Changed from the file's D. Raising the ceiling only to normal demand leaves no room for the spike; the maximum has to cover peak, and the warm pool removes the start-up delay.",
 478:"Changed from the file's D. The fleet is part Windows, and EFS cannot be mounted by Windows instances; FSx for Windows File Server serves both over SMB, and SSD suits the speed requirement.",
 480:"Changed from the file's D. Copies in another Region still sit in the same account, so an account compromise reaches them; cross-account copies are what protect against that, which the stem asks for explicitly.",
 487:"Separate VPN connections keep the two VPCs unconnected, which the stem requires; a transit gateway would join them unless carefully partitioned, and costs more.",
 494:"Expedited retrieval from Glacier Flexible Retrieval returns in 1-5 minutes, which is the only option inside the five-minute limit at archive prices.",
})

V.update({
 497:"C", 498:"D", 499:"D", 500:"A", 501:"D", 502:"A", 503:"B", 504:"C", 505:"C", 506:"C",
 507:"D", 508:"A", 509:"A", 510:"AB", 511:"DEF", 512:"AC", 513:"D", 514:"AC", 515:"C", 516:"A",
 517:"D", 518:"A", 519:"AC", 520:"A", 521:"B", 522:"A", 523:"A", 524:"B", 525:"A", 526:"B",
 527:"C", 528:"A", 529:"C", 530:"C", 531:"B", 532:"C", 533:"AE", 534:"C", 535:"A", 536:"C",
 537:"C", 538:"C", 539:"BD", 540:"C", 541:"A",
})
NOTES.update({
 500:"A presigned URL's maximum lifetime covers the seven days the consultant needs, and it grants access to that one object only.",
 527:"Write-through keeps the cache in step with the database, which is what 'up-to-date information' requires; lazy loading can serve a stale entry.",
 530:"Changed from the file's A. Mounting EFS is the documented way to give a function dependencies beyond the layer quota, it encrypts in transit, and it leaves no server to run.",
 533:"Memory is the only dial on a Lambda function - CPU scales with it - and provisioned concurrency removes the initialisation the connection setup pays.",
 541:"Changed from the file's D. Encryption cannot be switched on after a restore; it has to be applied when the snapshot is copied, which is what option A does.",
})

V.update({
 542:"A", 543:"A", 544:"D", 545:"D", 546:"D", 547:"C", 548:"D", 549:"A", 550:"A", 551:"A",
 552:"A", 553:"D", 554:"C", 555:"A", 556:"C", 557:"B", 558:"B", 559:"C", 560:"D", 561:"AB",
 562:"A", 563:"AC", 564:"D", 565:"B", 566:"C", 567:"CDF", 568:"D", 569:"BE", 570:"C", 571:"D",
 572:"A", 573:"AB", 574:"D", 575:"D", 576:"A", 577:"D", 578:"C", 579:"A", 580:"AC", 581:"C",
 582:"C", 583:"A", 584:"A", 585:"A", 586:"A",
})
NOTES.update({
 546:"Changed from the file's C. Provisioned concurrency cannot exceed reserved concurrency, so that combination is invalid, and provisioned concurrency is charged while reserved concurrency is not.",
 548:"Changed from the file's A. A security group in one Region cannot reference a security group in another, over peering or a transit gateway, so the rule has to use the peer CIDR.",
 564:"Changed from the file's C. Throughput that grows with the size of the file system is bursting mode; provisioned throughput is a fixed figure you set.",
 567:"Changed from the file's B,D,E. A hosted zone or an API endpoint per user is the opposite of operationally efficient; one wildcard certificate, one custom domain name and one wildcard alias cover every user.",
 574:"Interface endpoints cost more than a NAT gateway per hour, but NAT still sends traffic out through public addressing, which the stem forbids.",
})

V.update({
 587:"A", 588:"A", 589:"C", 590:"B", 591:"D", 592:"B", 593:"D", 594:"B", 595:"B", 596:"B",
 597:"A", 598:"D", 599:"B", 600:"C", 601:"C", 602:"B", 603:"C", 604:"CE", 605:"C", 606:"A",
 607:"D", 608:"A", 609:"D", 610:"D", 611:"C", 612:"A", 613:"C", 614:"C", 615:"A", 616:"D",
 617:"BE", 618:"A", 619:"CD", 620:"C", 621:"B", 622:"BE", 623:"A", 624:"DE", 625:"D", 626:"CD",
 627:"D", 628:"AE", 629:"A", 630:"C", 631:"B",
})
NOTES.update({
 591:"Changed from the file's B. Throttling protects the service by rejecting requests, which loses enrichments; caching on the customer key cuts the request volume while every message still gets its data. HTTP APIs also have no response caching.",
 594:"Changed from the file's D. The database metrics are clean and the load is write heavy, so a read cache addresses nothing; random slow responses under a scheduled scaling policy point at capacity that does not follow demand.",
 600:"Changed from the file's A. API keys and usage plans exist only on REST APIs, not HTTP APIs, and the stem requires API keys.",
 604:"The option list had two answers in one cell; forcing TLS on RDS for PostgreSQL is the rds.force_ssl parameter in a parameter group, and it is static, so the instance must restart.",
 608:"An EC2 Instance Savings Plan discounts more deeply than a Compute Savings Plan for a workload that stays in one instance family.",
 617:"Changed from the file's B,D. Resizing on a schedule leaves new uploads unprocessed for as long as an hour; an S3 event notification resizes each image as it lands.",
 621:"Changed from the file's C. A synchronous API Gateway integration times out at 29 seconds and the translation takes six minutes, so the invocation has to be asynchronous.",
 628:"Changed from the file's B,E. Secrets Manager has no gateway endpoint, so both use interface endpoints, and interface endpoints are reached through a security group rather than a route table entry.",
})

V.update({
 632:"D", 633:"D", 634:"D", 635:"C", 636:"C", 637:"AC", 638:"A", 639:"C", 640:"B", 641:"D",
 642:"C", 643:"A", 644:"C", 645:"C", 646:"A", 647:"D", 648:"D", 649:"B", 650:"B", 651:"D",
 652:"A", 653:"A", 654:"B", 655:"D", 656:"A", 657:"AD", 658:"D", 659:"D", 660:"C", 661:"D",
 662:"D", 663:"A", 664:"C", 665:"A", 666:"C", 667:"B", 668:"AB", 669:"C", 670:"C", 671:"A",
 672:"B", 673:"B", 674:"D", 675:"C", 676:"C",
})
NOTES.update({
 634:"Hundreds of documents behind CloudFront is the signed cookie case; a signed URL covers one file at a time.",
 642:"Kept the file's C. Strictly, HTTP APIs support throttling but not usage plans - read the option as throttling - and Express workflows are the cheaper choice for short, bursty runs.",
 659:"Encryption at rest on a DAX cluster can only be set when the cluster is created, so the cluster has to be replaced.",
 661:"Changed from the file's C. The stem says the data is relational, which rules out DynamoDB; Fargate also has no fifteen-minute ceiling for the long-running processes.",
 667:"Kept the file's B. Rehosting on a supported Windows Server keeps the .NET Framework code untouched; containerising a 2012-era application is possible but is more work, not less.",
 676:"Standard-IA retrieves immediately, which the five-minute promise needs; Glacier Flexible bulk retrieval takes hours.",
})

V.update({
 677:"B", 678:"C", 679:"C", 680:"D", 681:"A", 682:"C", 683:"C", 684:"D", 685:"D", 686:"C",
 687:"A", 688:"C", 689:"A", 690:"B", 691:"ABD", 692:"D", 693:"C", 694:"A", 695:"A", 696:"D",
 697:"D", 698:"C", 699:"A", 700:"C", 701:"C", 702:"AC", 703:"C", 704:"BE", 705:"D", 706:"D",
 707:"C", 708:"A", 709:"B", 710:"A", 711:"C", 712:"A", 713:"A", 714:"CD", 715:"D", 716:"A",
 717:"B", 718:"BC", 719:"BC", 720:"A", 721:"D",
})
NOTES.update({
 684:"Changed from the file's A. The application speaks AMQP and runs on Kubernetes; EKS with Amazon MQ preserves both, while ECS with SQS means rewriting the messaging layer.",
 690:"Changed from the file's C. An ECR login token is valid for twelve hours, not two; an explicit deny in a repository policy copied from the template repository does explain the failure.",
 693:"Setting the maximum to the baseline would stop the group scaling at all; leaving headroom above a reserved baseline is what absorbs the surges.",
 701:"Changed from the file's A. A cost and usage report on its own cannot attribute spend to a project - that needs activated cost allocation tags, and cost categories group them across accounts.",
 705:"Changed from the file's B. The stem asks only to match the existing hourly backups; a read replica and continuous backups exceed that and cost more.",
 714:"Changed from the file's A,C. Weighted routing sends a fixed share of traffic regardless of where a user is, so it does not reduce latency; a CDN does.",
 716:"Partial work can be lost, which is what makes core nodes on Spot acceptable here.",
 720:"An anycast IP address stays the same through a failover, so no resolver cache can send a client to the failed Region.",
})

V.update({
 722:"D", 723:"A", 725:"C", 726:"C", 727:"D", 728:"B", 729:"D", 730:"D", 731:"D", 732:"ACF",
 733:"A", 734:"C", 735:"C", 736:"B", 737:"D", 739:"D", 740:"B", 741:"B", 742:"A", 743:"B",
 744:"D", 745:"A", 746:"BE", 747:"C", 748:"A", 749:"A", 750:"D", 751:"C", 752:"C", 753:"C",
 754:"A", 755:"C", 756:"D", 757:"AE", 759:"D", 760:"A", 761:"B", 762:"C", 763:"A", 764:"C",
 765:"B", 766:"D", 767:"D", 768:"A", 769:"D",
})
NOTES.update({
 730:"Every component in the path has to tolerate the idle hour, not just the load balancer in front of the application.",
 734:"The jobs cannot be disrupted, which rules Spot out; the data is read during its first 30 days, so it starts in Standard rather than an archive class.",
 741:"Retrieval within minutes rules out Deep Archive, whose fastest option is measured in hours; Glacier Flexible Retrieval offers expedited retrieval in 1-5 minutes.",
 750:"A 60-second recovery time means the second Region must already be running - a warm standby - because launching instances takes longer than that.",
 751:"Service-managed users in Transfer Family accept the SSH public keys the clients already use, so neither the users nor their process changes.",
 756:"A Compute Savings Plan is the only commitment that covers both EC2 and the growing Lambda usage, and the functions must join the VPC to reach private instances.",
})

V.update({
 770:"D", 772:"B", 773:"D", 774:"B", 775:"C", 776:"B", 777:"D", 778:"AB", 779:"B", 780:"A",
 781:"BD", 782:"D", 783:"A", 784:"D", 785:"B", 786:"B", 787:"D", 788:"B", 789:"B", 790:"D",
 791:"D", 792:"A", 793:"BEF", 794:"D", 795:"B", 796:"B", 797:"B", 798:"C", 799:"A", 800:"BEF",
 801:"D", 802:"B", 803:"C", 804:"C", 805:"B", 806:"A", 807:"D", 808:"B", 809:"B", 810:"B",
 811:"A", 812:"A", 813:"B", 814:"CD", 815:"B",
})
NOTES.update({
 777:"Option B would add SSH to the list of authorised ports, which permits exactly what the stem forbids. Firewall Manager's security group audit policy with the public-access-denied list is the control built for this.",
 778:"Option A says private subnet where a NAT gateway must sit in a public one; read as a NAT gateway in the same Availability Zone as the cluster, which removes the cross-zone charge, while the gateway endpoint takes same-Region S3 traffic off NAT altogether.",
 784:"A header only changes what is cached when it is part of the cache key, which is the cache policy; an origin request policy forwards it without varying the cache.",
 789:"ACM public certificates cannot be exported onto an instance, so the back half of the connection uses a self-signed certificate, which the load balancer does not validate.",
 798:"The files are generated once per request, so nothing can be cached; compressing them on the way out is what reduces the bytes transferred.",
 800:"A legal hold lasts until it is removed, which matches 'until the PII is reviewed'; a fixed retention period would have to guess how long the review takes.",
 805:"Peering has no bandwidth ceiling of its own, while a transit gateway attachment is capped, so peering gives the higher throughput for three VPCs.",
})

V.update({
 816:"D", 817:"C", 818:"D", 819:"A", 820:"D", 821:"B", 822:"D", 823:"C", 824:"AD", 825:"B",
 826:"A", 827:"A", 828:"D", 829:"B", 830:"A", 831:"D", 832:"D", 833:"D", 834:"C", 835:"D",
 836:"C", 837:"B", 838:"D", 839:"D", 840:"A", 841:"CD", 842:"D", 843:"C", 844:"A", 845:"C",
 846:"D", 847:"C", 848:"D", 849:"B", 850:"B", 851:"A", 852:"A", 853:"B", 854:"A", 855:"C",
 856:"A", 857:"B", 858:"C", 859:"B", 860:"B",
})
NOTES.update({
 823:"Exactly-once processing needs a FIFO queue, and an S3 event notification cannot target one directly, so the event goes through EventBridge.",
 838:"Replication Time Control is what backs the 15-minute replication commitment the stem's 30-minute target depends on, and the access point gives the single identifier.",
 841:"The option list absorbed the '(Select TWO.)' instruction into option A, which reads 'Add AWS Global Accelerator'.",
 860:"Provisioned concurrency is what removes the Java cold-start latency; reserved concurrency only caps how many copies run.",
})

V.update({
 861:"C", 862:"D", 863:"D", 864:"B", 865:"D", 866:"D", 867:"B", 868:"A", 869:"A", 870:"A",
 871:"B", 872:"D", 873:"A", 874:"C", 875:"A", 876:"C", 877:"BE", 878:"AE", 879:"A", 880:"D",
 881:"C", 882:"A", 883:"BC", 884:"A", 885:"C", 886:"B", 887:"B", 888:"A", 889:"D", 890:"C",
 891:"A", 892:"C", 893:"C", 894:"A", 895:"C", 896:"AD", 897:"B", 898:"A", 899:"C", 900:"A",
 901:"B", 902:"C", 903:"D", 904:"C", 905:"D",
})
NOTES.update({
 862:"An S3 gateway endpoint carries no IPv6 traffic, so the IPv6 instances need the S3 interface endpoint; DynamoDB is reached by its gateway endpoint.",
 869:"Glacier Instant Retrieval already serves the files in milliseconds during year one and costs far less than S3 Standard, and Deep Archive is the cheapest home for years two to seven.",
 874:"The blue/green option is the only one that tests the schema on a synchronised copy and switches over in seconds; the OCR reversed the colour names in the last sentence.",
 877:"Option C carries the text of the lost option D (an AWS Batch job); Batch Replication covers the 500 existing objects and CRR covers every future one.",
 891:"Glacier Flexible Retrieval's standard retrieval lands in 3-5 hours, inside the stated limit, while Deep Archive needs 12.",
}) 

V.update({
 906:"B", 907:"C", 908:"C", 909:"B", 910:"B", 911:"C", 912:"C", 913:"D", 914:"B", 915:"C",
 916:"C", 917:"C", 918:"A", 919:"B", 920:"D", 921:"B", 922:"A", 923:"BC", 924:"B", 925:"B",
 926:"C", 927:"A", 928:"D", 929:"B", 930:"BE", 931:"D", 932:"D", 933:"B", 934:"A", 935:"A",
 936:"B", 937:"A", 938:"B", 939:"AE", 940:"A", 941:"A", 942:"C", 943:"C", 944:"A", 945:"B",
 946:"D", 948:"C", 949:"B", 950:"DEF",
})
NOTES.update({
 913:"Compliance mode is the only setting no one, including the root user, can shorten, which is what a ransomware defence needs; Object Lock also requires versioning.",
 922:"RequestCount is a standard ALB metric, so nothing extra has to be published; the custom-metric option would add CloudWatch charges for the same behaviour.",
 935:"Fast snapshot restore has to be enabled in the Availability Zone the volumes will be created in, which here is the second one.",
 941:"gp3 provisions IOPS separately from capacity and costs less than io1 at 15,000 IOPS; gp2 ties IOPS to size, which is what the stem rules out.",
 946:"The stem demands redundancy for the whole lifecycle, which rules out One Zone-IA, and instant access after archiving, which rules out Flexible Retrieval.",
 947:"Dropped: OCR lost the 'invoke a Lambda function when a message is available in the queue' option, which is one of the three required answers.",
})

V.update({
 951:"B", 952:"D", 953:"C", 957:"C", 958:"A", 959:"C", 960:"C", 961:"C", 962:"AEF", 963:"A",
 964:"B", 965:"C", 966:"A", 967:"D", 968:"BDE", 969:"B", 970:"B", 971:"BE", 972:"B", 973:"A",
 974:"C", 975:"B", 976:"A", 977:"C", 978:"B", 979:"A", 980:"D", 981:"B", 982:"BE", 983:"CD",
 984:"C", 985:"B", 986:"B", 987:"B", 988:"B", 989:"C", 990:"A", 991:"A", 992:"D", 993:"D",
 994:"D", 995:"A",
})
NOTES.update({
 954:"Dropped with 955 and 956: three CompTIA Security+ questions that the source file mixed in among the AWS ones.",
 962:"Options E and F arrived merged in one cell ('... transit VIF. CF. Share the transit gateway ...') and were split back apart.",
 971:"Only the primary record needs the health check; the secondary takes over when that check fails.",
 977:"The company wants to generate keys but not run key storage or the crypto, which is exactly a KMS customer managed key used through SSE-KMS.",
 986:"ACM certificates cannot be exported, so the instances need a third-party certificate for the second hop.",
 990:"Redshift Spectrum reads S3, not Redshift's own tables, which is what makes option D wrong.",
 995:"The runtime is growing past what Lambda's 15-minute ceiling and memory-bound CPU can serve; Fargate keeps it serverless at lower cost than EC2.",
})

V.update({
 996:"D", 997:"B", 998:"B", 999:"D", 1000:"D", 1001:"A", 1002:"B", 1003:"D", 1004:"D", 1005:"C",
 1006:"B", 1007:"B", 1008:"D", 1009:"C", 1010:"D", 1011:"A", 1012:"D", 1013:"D", 1014:"A", 1015:"D",
 1016:"A", 1017:"B", 1018:"D", 1019:"C", 1020:"A", 1021:"D", 1022:"C", 1023:"AD", 1024:"CEF", 1025:"B",
 1026:"B", 1027:"A", 1028:"A", 1029:"A", 1030:"A", 1031:"D", 1032:"C", 1033:"A", 1034:"D", 1035:"B",
 1036:"B", 1037:"A", 1038:"A", 1039:"BCE", 1040:"B",
})
NOTES.update({
 996:"SnapMirror copies at the block level, so 60 million small files move in a fraction of the time DataSync would need to walk them one by one.",
 1003:"The error is throttling, not a cold start, so the queue absorbs the burst and reserved concurrency guarantees the function its own slice of the account limit.",
 1006:"A step already runs 20-30 minutes, which is past Lambda's 15-minute ceiling, so the Lambda options cannot run this workload at all.",
 1011:"Everything an IAM policy does not allow is already denied, so the single Allow on rds:* is enough and the extra Deny statements are noise.",
 1018:"DynamoDB's export to S3 reads from the continuous backup rather than the table, so it does not touch the provisioned throughput.",
 1024:"The runtime role trusts the cluster's EC2 instance profile, the instance profile is given permission to assume the runtime roles, and the security configuration turns the feature on.",
 1036:"A NAT gateway would send the traffic out and back for nothing; a gateway endpoint keeps it on the AWS network, and directory buckets support gateway endpoints.",
 1039:"Options E and F arrived merged in one cell ('... application tier- UF. Configure ...') and were split back apart.",
})

V.update({
 1041:"D", 1042:"D", 1043:"B", 1044:"C", 1045:"C", 1046:"A", 1047:"C", 1048:"B", 1049:"C", 1050:"A",
 1051:"D", 1052:"C", 1053:"A", 1054:"D", 1055:"B", 1056:"A", 1057:"B", 1059:"D", 1060:"C", 1061:"C",
 1062:"D", 1063:"ACE", 1064:"C", 1065:"A", 1066:"D", 1067:"D", 1068:"A", 1069:"A", 1070:"A", 1071:"C",
 1072:"A", 1073:"C", 1074:"B", 1075:"C", 1076:"C", 1077:"C", 1078:"D", 1079:"A", 1080:"D", 1081:"D",
 1082:"A", 1083:"C", 1084:"D", 1085:"D",
})
NOTES.update({
 1047:"FSx for NetApp ONTAP serves the same volume over NFS and SMB at once, which is what removes the second copy without touching either application.",
 1051:"A CloudFront Function cannot call out to validate a token and option C also strips the API's own authorizer, which is the opposite of zero trust.",
 1063:"ElastiCache would have to be called by the application, and the stem forbids changing it; Aurora MySQL is a drop-in replacement that adds read replicas.",
 1067:"Hybrid Nodes keeps the control plane managed by AWS while the company's own VMs stay the nodes and the company keeps running the on-premises network.",
 1074:"Changed from the file's C. The application is stateful, so Spot interruptions would drop sessions, and an EC2 Instance Savings Plan discounts a predictable single-family workload more deeply than a Compute Savings Plan.",
 1085:"Every option says the filter policy rewrites the body, which no filter policy does; D is still the only one that routes each seller their own updates with a subscription filter.",
})

V.update({
 1086:"D", 1087:"A", 1088:"C", 1089:"D", 1090:"A", 1091:"BCD", 1092:"D", 1093:"A", 1094:"C", 1095:"A",
 1096:"A", 1097:"B", 1098:"D", 1099:"D", 1100:"D", 1101:"A", 1102:"D", 1103:"C", 1104:"C", 1105:"DE",
 1106:"A", 1107:"B", 1108:"C", 1109:"D", 1110:"B", 1111:"A", 1112:"B", 1113:"C", 1114:"A", 1115:"A",
 1116:"B", 1117:"B", 1118:"A", 1119:"B", 1120:"B", 1121:"D", 1122:"D", 1123:"C", 1124:"AC", 1125:"B",
 1126:"BD", 1127:"C", 1128:"B", 1129:"B", 1130:"B",
})
NOTES.update({
 1095:"The application is proprietary x86 and cannot be recompiled, so every Graviton recommendation is off the table.",
 1096:"Jobs run up to 30 minutes, past Lambda's 15-minute ceiling, so the queue has to feed Fargate tasks.",
 1105:"Changed from the file's C. A standard accelerator sends traffic to an endpoint and lets the load balancer pick the instance; only a custom routing accelerator pins the users of one session to the same EC2 instance, which is what the stem asks for.",
})

V.update({
 1131:"C", 1132:"BD", 1133:"D", 1134:"CD", 1135:"D", 1136:"A", 1137:"C", 1138:"AC", 1139:"B", 1140:"A",
 1141:"A", 1142:"C", 1143:"B", 1144:"B", 1145:"D", 1146:"A", 1147:"A", 1148:"D", 1149:"B", 1150:"B",
 1151:"D", 1152:"C", 1153:"D", 1154:"D", 1155:"D", 1156:"D", 1157:"AD", 1158:"D", 1159:"AE", 1160:"CD",
 1161:"A", 1162:"B", 1163:"B", 1164:"C", 1165:"D", 1167:"A", 1168:"B", 1169:"C", 1170:"B", 1171:"D",
 1172:"C", 1173:"AD", 1174:"C", 1175:"D", 1176:"C", 1177:"A", 1178:"A", 1179:"D", 1180:"B",
})
NOTES.update({
 1136:"Deep Archive's standard retrieval is about 12 hours, inside the 24-hour limit the stem sets.",
 1138:"Kept the file's A and C. Option E's Glacier transition could be cheaper for large objects, but telemetry arrives as many small objects, where per-object transition and minimum-size charges eat the saving.",
 1156:"The unique IDs are the problem SnapStart creates: every restored copy would share one. Moving that line into the handler fixes it; the hook AWS actually documents for this is afterRestore rather than the pre-snapshot one the option names.",
 1161:"Kept the file's A even though DAX buys nothing for a report run once a quarter, because option B replicates the table across Regions, which multiplies the very storage cost the stem asks to reduce.",
 1171:"Changed from the file's C. Concurrency scaling skips queries that build temporary tables, which is exactly what these jobs do, and the option keeps the large cluster running, so it saves nothing. Serverless is the one that charges nothing while idle.",
 1176:"The trust points outward from the AWS domain, so AWS trusts on-premises identities and not the reverse, which is what keeps AWS users out of the on-premises domain.",
})

V.update({
 1181:"C", 1182:"B", 1183:"C", 1184:"C", 1185:"A", 1186:"C", 1187:"C", 1188:"B", 1189:"D", 1190:"A",
 1191:"C", 1192:"CD", 1193:"ABF", 1194:"C", 1195:"D", 1196:"B", 1197:"A", 1198:"D", 1199:"C", 1200:"AC",
 1202:"A", 1203:"C", 1205:"A", 1206:"C", 1207:"D", 1208:"C", 1209:"A", 1210:"D", 1213:"AC", 1215:"B",
 1216:"A", 1217:"A", 1218:"D", 1219:"A", 1220:"C", 1221:"BE",
})
NOTES.update({
 1191:"One security group on both ends with a rule referencing itself is the standard pattern; option A opens the wrong direction on the Lambda's group.",
 1192:"Changed from the file's D,E. EventBridge cannot take an SNS topic as an event source, so option E has nothing to trigger it; the topic policy has to permit the cross-account subscription instead.",
 1200:"Changed from the file's C,D, which were the same answer twice after OCR duplicated the option; the duplicate was removed. Discount sharing is a management-account billing preference, so option A is needed for the Savings Plan to reach the new accounts.",
 1205:"The files are read fewer than four times a year, so Glacier Instant Retrieval's storage price wins and Intelligent-Tiering only adds a monitoring charge per object.",
 1211:"Dropped: OCR lost option A ('use the S3 Standard storage class for the temporary location'), one of the three answers.",
 1216:"The documents pass 1 MB, which is over DynamoDB's 400 KB item limit, so the document database is the only one of the four that can hold them.",
})

if __name__ == "__main__":
    print("answers recorded:", len(V))

V.update({451:"AC", 1224:"C", 1225:"BD", 1226:"A", 1227:"B", 1228:"A"})
NOTES.update({
 1224:"Two instances in each of two Availability Zones is what keeps at least two running when one zone fails; a minimum of two would leave one.",
})

NOTES.update({
 332:"Changed from the file's B. A Lambda layer is capped at 50 MB unzipped and is not a file system, so it cannot hold a growing EFS dataset; peering the VPCs lets the function mount the file system across accounts.",
 606:"Changed from the file's B. Random prefixes only spread request rate; they do not change S3 Standard's latency, while Express One Zone is the tier built for single-digit milliseconds.",
})

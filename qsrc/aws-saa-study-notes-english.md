# AWS Solutions Architect Associate — Study Notes

These notes are written as flowing prose rather than dense bullet points, so that a voice assistant can read them aloud naturally. Acronyms are spelled out the first time they appear in each section.

## Regions, Availability Zones, and Edge Locations

A Region is a geographic location where Amazon's physical data centers sit. As of 2018 there were about nineteen regions. When choosing a region, you should weigh five factors. First is latency: response speed depends on the geographic distance between the user and the region, so the closer the region is to the user, the lower the latency will be. Second is price: prices vary by region, since infrastructure costs more in some places than others, which makes AWS services more expensive there too. Third is service availability, since not every service is available in every region. Fourth is compliance: some countries have regulatory laws requiring that a company's data be stored within that country's borders, so if such a law applies to you, you must choose a region located inside your own country.

Availability Zones are zones within a region, and each one contains several of Amazon's physical data centers. As of 2018 there were roughly fifty-seven availability zones across all regions. Every availability zone is connected to the other availability zones in the same region through fast, resilient fiber connections. Finally, an Edge Location is an AWS endpoint used for caching content.

## Accessing and Managing AWS

There are three ways to control and operate AWS. The AWS Management Console is the standard way to work, using a graphical user interface. The AWS Command Line Interface, or CLI, lets you control AWS from a terminal, make API calls, and write scripts; it can be used from anywhere in the world, but you need to enable access through IAM roles. The AWS Software Development Kits, or SDKs, are extension packages you can install and use to work with AWS across a variety of programming languages.

## Security and the AWS Shared Responsibility Model

Protection of information on AWS is split between the customer and Amazon. Amazon is responsible for protecting the cloud itself, meaning it protects and controls every component from data centers, to availability zones, to regions, all the way down to the physical servers inside the data center. The customer is responsible for protecting what they put inside the cloud, meaning access permissions to their own files and virtual servers, and for performing their own backups.

Multi-factor authentication, or MFA, is used to verify the identity of a user logging into the system, and it should always be enabled on the root account. There are three methods of performing MFA: virtual MFA, which is software running on a phone or another device that generates a one-time login token, similar to RSA; a hardware device, such as a magnetic card, that generates a one-time login code; and a U2F device, which is a physical key plugged into a computer's USB port.

## IAM Basics

IAM, the Identity and Access Management service, is a universal AWS service, meaning it is not tied to any particular region. It handles authentication, which verifies who you are, and authorization, which controls what you're allowed to do, and together these let you control access to your AWS account and to actions such as API calls to services like S3. In fact, every action on AWS is technically an API call.

With IAM you can create IAM users and manage their permission policies. A newly created user starts with no permissions at all. Every new user is assigned an access key ID and a secret access key, which are used to access AWS through API calls and the command line, but they cannot be used to log into the web console. You can only view these keys once, so you must save a copy somewhere safe. The root user has every possible permission.

You can also create permission groups and attach them to the users you want; each policy is essentially a JSON file. Role-based access lets you create predefined permission templates, for example based on job function, and apply them automatically when needed, giving a user permission to perform actions not otherwise defined for their account. This approach is far more secure than using access keys and secret access keys on every EC2 instance, it's easier to manage, roles can be attached to EC2 instances after they're created through the console or the CLI, and roles can be used in any region.

## AWS Organizations and Consolidated Billing

AWS Organizations lets you manage multiple AWS accounts belonging to an organization. You can create an Organizational Unit, or OU, and apply policies with specific permissions to it, and then every AWS account created under that OU inherits those policy settings. You can also manage billing across all the organization's accounts; you'll receive a separate invoice for each AWS account, which makes it easier to track different charges, and you'll also get volume discount pricing. Recommended practices here are to always use MFA on the root user, always use strong and complex passwords on the root user, and to use the paying account strictly for billing purposes and never for running any actual resources. You can also enable or disable AWS services using Service Control Policies, or SCPs, applied either to an OU or to individual AWS accounts.

## Amazon S3

S3 stands for Simple Storage Service. It's a cloud storage infrastructure for storing and retrieving any amount of data, at any time, from anywhere on the network. S3 offers very high durability of ninety-nine point nine nine percent, low prices, and almost unlimited growth options. Access to S3 isn't like accessing a regular disk the way you would with EBS; instead you access objects through the API or through third-party tools. When you upload a file to S3, you receive an HTTP two hundred status code as confirmation. A single object can range in size from zero bytes up to five terabytes.

Files are stored in buckets, which you can think of as folders in the cloud, and you can attach access permissions to them. S3 is a global service with a universal namespace, so every bucket needs a globally unique name. Note that you cannot install operating systems on S3; that's only possible on EC2.

Objects in S3 are made up of several components: the key, which is the file's name; the value, which is the actual data the file consists of; the version ID, used for version control; metadata, which is information about the file such as its type; and additional sources like access control lists and torrent links.

When you upload a new file to S3 and immediately read it afterward, you'll be able to read it without any problem. But if you update an existing file in S3 and immediately read it afterward, you might get either the old or the new version, because in principle, changes to existing files can take some time to take effect. By default, all external access to files in S3 is blocked. You can encrypt an entire bucket, or just the files inside it.

Regarding encryption: for encryption in transit, SSL and TLS are used. For encryption at rest, there are three options: SSE-S3, which uses S3-managed keys; SSE-KMS, which uses keys managed through the AWS Key Management Service; and SSE-C, server-side encryption with customer-provided keys. There's also client-side encryption, where the client is responsible for encrypting the files before uploading them to S3.

You can enable version control and upload multiple versions of the same file; by default you'll always see the latest version, and clicking "list versions" lets you see previous ones. You can only suspend versioning, not disable it completely. Note that making a file public only affects the latest version; to make other versions public too, you'd need to do that separately for each version. To delete a file from a previous version, you click delete to mark it, and then repeat the action and specify "permanent."

You can apply lifecycle management to automatically move files between storage tiers based on rules you set in advance, in order to save on storage costs. Note that moving files to the infrequent-access or one-zone infrequent-access tiers requires that at least thirty days have passed.

S3 Object Lock lets you store files in S3 using a write-once, read-many model, known as WORM. This feature is used to meet organizational regulatory requirements or to add an extra layer of security that prevents accidental deletion. There are several modes: Governance mode, where most users are prevented from modifying or deleting files while authorized users can still make changes; Compliance mode, where no user, including the root user, can delete or modify files during the retention period, which is a predefined length of time; Legal Holds, which similarly prevent deletion or modification but with no retention period, and instead remain in effect until removed by any user with the S3 PutObjectLegalHold permission; and Glacier Vault Lock, which lets you apply policies to Glacier vaults and lock them against change or deletion, and once locked they can never be modified again.

For S3 performance, it's recommended to use multipart upload for any file over one hundred megabytes, and it's mandatory for any file larger than five gigabytes.

S3 Select lets you use a simple SQL query to pull out just the part of the data you need, by specifying rows and columns, instead of retrieving the whole object, which provides up to four hundred percent faster performance and eighty percent cost savings. There's also an equivalent feature for Glacier, called Glacier Select.

There are three ways to share cross-account access to an S3 bucket: using IAM combined with bucket policies, which supports programmatic access only; using IAM combined with bucket access control lists, also programmatic access only; and using cross-account IAM roles, which supports both programmatic access and console access.

Cross-Region Replication lets you replicate objects from a bucket in one region to a bucket in another region, and you can also replicate between buckets within the same region, whether they belong to the same AWS account or different ones. To enable this feature, versioning must be turned on in both buckets. Files that already existed before you enabled replication will not be replicated, only new files going forward. Files that get updated or modified afterward are replicated automatically. Files marked for deletion are not replicated, and if you've deleted specific versions of a file through version control, those deletions aren't replicated either.

S3 Transfer Acceleration lets you upload files to S3 faster by routing them through an edge location instead of uploading directly to the region; the file goes to the nearest edge location and travels from there to the relevant region over Amazon's backbone connection, which usually provides much higher upload speed.

## AWS DataSync

AWS DataSync lets you migrate data from a company's own data center to AWS. It's used to transfer large volumes of data from a customer's site into AWS. It works with NFS and SMB file shares, you can schedule replications on an hourly, daily, or weekly basis, and you need to install the DataSync agent to begin replication. It can also be used to replicate from one EFS file system to another.

## CloudFront

CloudFront is used to load content faster by using edge locations. The first user who accesses some content has to reach the region where that content lives; the content is then copied to an edge location for a limited time, defined by a time-to-live value, and every other user who then requests that content gets much faster access, because they only need to reach the nearby edge location. Note that you can delete cached files, but you'll be charged for that operation.

A few key terms: an Edge Location is an AWS endpoint used for caching, and importantly, edge locations aren't read-only, you can write to them as well. The Origin is the source of the files, and it can be an S3 bucket, EC2, an Elastic Load Balancer, or Route 53. A Distribution is the name given to a CDN, which is a collection of several edge locations. A Web Distribution is typically used for websites, and RTMP is typically used for streaming media.

You can restrict access to shared content using signed URLs or signed cookies. A signed URL is used for access to a single file, one file equals one URL. A signed cookie is used for access to multiple files, one cookie equals multiple files. Whichever one you use, you'll need to add a policy, which can include an expiration date for the URL, an IP address range, and trusted signers. If the origin you want to share is EC2, you'd use CloudFront; if it's S3, you'd use an S3 signed URL instead.

## Snowball and Storage Gateway

Snowball is essentially a type of AWS hard drive that you connect to your local environment to transfer material to or from S3; it comes in sizes ranging from fifty terabytes up to one exabyte, which is beyond a petabyte.

Storage Gateway lets you work in a hybrid-cloud setup, combining AWS and on-premises environments, and it enables replication from a local data center into S3. There are three types. File Gateway is used for transferring files, which get stored directly on S3. Volume Gateway has two variants: Stored Volumes, where the entire dataset is stored on-site and backed up asynchronously to S3; and Cached Volumes, where the entire dataset is stored on S3 while the most frequently accessed files are cached locally. Virtual Tape Library Gateway handles replication from backup tapes to S3.

## Athena versus Macie

Athena is an interactive query service that lets you run SQL queries against data stored in S3. It's serverless, so there's no need to provision space or virtual machines, and you pay per query. It's mainly used for analyzing logs stored in S3.

Macie uses artificial intelligence to analyze data in S3 and helps identify personally identifiable information, meaning sensitive data containing identifying details or payment information. It can also be used to identify CloudTrail logs showing suspicious API calls. It includes a main dashboard along with reports and alerts, and it's excellent for PCI-DSS, the secure online credit-card payment standard, and for preventing identity theft.

## Amazon EC2

EC2 stands for Elastic Compute Cloud, Amazon's cloud computing service, and it lets you run virtual machines of various sizes and types. These machines can run different operating systems, and there are four payment options. On-Demand billing charges by the hour of usage, or even by the second, with no commitment at all. Reserved capacity allocates a set amount of resources in advance that you can use at an hourly rate with a significant discount, with contracts available for one year or three years; note that you can sell unused Reserved Instances on the Reserved Instance Marketplace, and Convertible Reserved Instances let you change the instance family and other parameters associated with your reservation at any time. Spot Instances let you bid the price you're willing to pay, allowing even greater savings if the applications you want to run have flexible start and stop times. Dedicated Hosts are physical EC2 servers allocated entirely for your use, which can help you save money by using an existing server instead of allocating brand-new ones.

You can run EC2 instances across five different geographic areas, namely the eastern and western United States, Europe, and Asia, and within each geographic area there are two or three availability zones, comparable to server farms, to give you higher durability.

If Amazon terminates your EC2 instance, you won't be charged for the partial usage of that instance, but if you shut it down yourself, you will be charged for whatever you used.

A few important reminders: termination protection is off by default, so the user needs to turn it on. For an EBS-backed instance, the default behavior is that the EBS volume gets deleted when the instance is terminated. You can encrypt the EBS root volume natively, and you can also use third-party software like BitLocker. You can also encrypt additional volumes beyond the root volume.

## Security Groups

Security Groups are responsible for security and access to an instance, functioning like a firewall; they allow entry from specific ports and specific IP addresses, and you can define inbound and outbound rules controlling traffic allowed into and out of the instance respectively. By default, all inbound traffic is denied and all outbound traffic is allowed. Once you change the rules, they take effect immediately. There's no limit on the number of instances in a single security group, and you can attach several security groups to a single instance. Security groups are stateful, meaning that if you define an inbound rule, a corresponding outbound rule is automatically applied, and vice versa. You cannot block a specific port or a specific IP address through a security group; for that you need Network Access Control Lists. Also, security groups only support allow rules, not deny rules.

## Elastic Block Store, EBS

EBS stands for Elastic Block Store, which provides virtual "disks," called volumes, that can be configured separately from your EC2 virtual machines. These disks can be attached to virtual machines and behave exactly like a normal disk. EBS is priced according to the disk's size and how much it's used. Beyond storing data, EBS also offers backup capabilities, based on S3, and snapshots, which are very useful during software updates.

A snapshot is an incremental backup, meaning it only saves the changes made since the last snapshot. Creating the very first snapshot can take some time because it has to contain all the instance's data, not just the changes, the way later snapshots do. To create a snapshot of an EBS root volume, you must stop the instance first, but you can create snapshots of other volumes while the instance is still running. You can create an AMI, an Amazon Machine Image, from a snapshot. You can resize EBS volumes dynamically while they're running, including changing the storage type and size. EBS volumes always live in the same availability zone as their instance. To move a volume from one availability zone to another, you follow these steps: create a snapshot of the volume, create an AMI from that snapshot, and then use that AMI when launching a new EC2 instance in the other availability zone.

EC2 instances that aren't EBS-backed are considered "temporary" machines that don't retain data after shutdown; they're effectively destroyed. If you want to run a machine you can turn on and off like a regular server and keep your changes after shutdown, the machine must be EBS-backed, which makes it slightly more expensive. As a rule of thumb, if throughput matters most to you, use HDD; if IOPS, meaning input and output operations per second, matter most, use SSD.

Comparing the different EBS volume types: solid-state drives include General Purpose SSD, best for most workloads, with sizes from one gibibyte up to sixteen tebibytes and up to sixteen thousand IOPS; and Provisioned IOPS SSD, the highest-performance option, designed for databases, with the same size range and up to sixty-four thousand IOPS. Hard disk drives include Throughput Optimized HDD, a low-cost option for frequently accessed, throughput-intensive workloads like big data and data warehouses, sized from five hundred gibibytes to sixteen tebibytes with up to five hundred IOPS; Cold HDD, the lowest-cost HDD option for infrequently accessed data such as file servers, same size range, up to two hundred fifty IOPS; and EBS Magnetic, the previous generation, for workloads where data is accessed infrequently, sized from one gibibyte to one tebibyte with forty to two hundred IOPS.

## Instance Store

Instance Store is another type of storage besides EBS, sometimes called ephemeral storage. You cannot stop volumes of this type; if the underlying storage behind them fails, all the data is lost. Unlike instance store, EBS volumes can be stopped without losing data. Both types of volumes can be rebooted without losing data. By default, the root volume of both types is deleted when the instance is terminated, but with EBS, you can configure the root volume's data to persist even after termination.

## ENI versus Enhanced Networking versus EFA

ENI stands for Elastic Network Adapter, a virtual network card, used for basic networking needs, for example when you need a separate management address or additional addresses or networks at a low price. Enhanced Networking is used for network speeds between ten and one hundred gigabits per second, for situations that need a fast, reliable connection; there's no extra charge for using this network card, and you can use it via ENA or VF, though ENA is always preferred over VF when available. The Elastic Fabric Adapter, or EFA, is for use cases requiring especially high performance, high performance computing, and for machine-learning applications, or whenever you need to bypass the operating system. This OS bypass lets high performance computing and machine learning applications skip past the operating system's kernel, currently supported only on Linux, to talk directly to the EFA device, which makes usage much faster with lower latency.

## Amazon Data Lifecycle Manager and Encrypted Root Volumes

Amazon DLM, the Data Lifecycle Manager, is an automated process for backing up the data stored in your EBS volumes. You use Amazon DLM to create lifecycle policies in order to automate management of your snapshots.

Regarding encrypted root device volumes and snapshots: to encrypt a new root volume, you need to select the encrypted option when creating it. Note that if the EBS volume is encrypted, then all data moving between the EBS volume and the EC2 instance is encrypted as well. Snapshots of encrypted volumes are automatically encrypted. Volumes created by restoring an encrypted snapshot are also automatically encrypted. You can share snapshots, but only if they're unencrypted, and you can share these snapshots with other AWS accounts or make them public. To convert an existing root volume into an encrypted one, you follow these steps: create a snapshot of the volume, create a copy of the snapshot and choose the encrypt option, create an AMI from the encrypted copy of the snapshot, and then use that AMI to launch a new, encrypted EC2 instance.

## Spot Instances and Spot Fleets

Unlike the On-Demand approach we've focused on so far, with Spot Instances you're essentially trading on unused capacity on AWS, at a price that varies by region and demand, and as a result you pay an hourly rate roughly ninety percent lower than what you'd pay On-Demand, but you're not guaranteed that your EC2 instance will run for a long time. This feature is useful for any non-critical process that doesn't need persistent storage. You set a maximum price threshold you're willing to pay, and once that threshold is reached, you get a two-minute window to decide whether to shut down your instance or keep paying. You can use the Spot Block feature to prevent your instance from being terminated. A Spot Fleet is a collection of Spot Instances, and optionally On-Demand Instances as well, letting you enjoy a low price while still guaranteeing a certain level of availability when you need it.

## EC2 Hibernate

EC2 Hibernate lets you save the RAM contents to EBS if you want to pause an instance's activity and pick up immediately where you left off. Booting takes much less time because the operating system doesn't need to be reloaded. The instance's RAM must be under one hundred fifty gigabytes. The supported instance families are C3, C4, C5, M3, M4, M5, R3, R4, and R5. You can use this feature with instances running Windows, Amazon Linux 2 AMIs, and Ubuntu. You cannot hibernate for more than sixty days, and you can use hibernation with both On-Demand Instances and Reserved Instances.

## CloudWatch and CloudTrail

CloudWatch is a feature used for performance monitoring. It can monitor most AWS services, including your own applications running on AWS. When you enable it on EC2, it monitors events every five minutes by default. You can get notifications at one-minute intervals by enabling detailed monitoring. You can create CloudWatch alarms that generate notifications, and you can create dashboards, alarms, and events. To monitor custom metrics, you need to install the CloudWatch agent on the EC2 instance.

CloudTrail is a feature that lets you track actions taken on AWS, through both the console and the API, and it also lets you see the IP address the actions were made from. By default, all CloudTrail logs are encrypted using Amazon S3 server-side encryption.

## Bootstrap Scripts and Instance Metadata

Bootstrap scripts let you write a script that runs automatically when an EC2 instance is deployed. You add the script when configuring the EC2 instance, under Advanced Details, in the User Data field. Every script should begin with the shebang line pointing to bash.

Instance Metadata is used to retrieve information about a specific instance. You connect via SSH to the instance and, depending on what you need, run a curl command against the metadata endpoint or the user-data endpoint at the special address one-six-nine-dot-two-five-four-dot-one-six-nine-dot-two-five-four.

## EFS and FSx

EFS is AWS's file system service for EC2; it grows and shrinks automatically and can be shared and accessed by multiple EC2 instances at once. It supports the NFS version four point one protocol. You only pay for what you use, with no need to provision storage space in advance. It can scale up to petabytes, supports thousands of concurrent NFS connections, and its data is stored across several availability zones within a region. It supports read-after-write consistency. Note that it only supports Linux EC2 instances; for Windows, you'd use the SMB protocol through Amazon FSx for Windows.

Amazon FSx for Windows is used for Windows applications such as Microsoft SQL Server, Workspaces, IIS web server, SharePoint, or any other Windows application, and it works over the SMB protocol. Amazon FSx for Lustre is used for applications that require heavy processing power, such as financial models, and this feature can use S3 directly for storage.

## EC2 Placement Groups

A Clustered Placement Group is a cluster of instances located in the same availability zone. It's recommended for applications requiring low latency, high bandwidth, or both, and the goal here is to pack instances as close together as possible to guarantee low latency.

A Spread Placement Group is a "cluster" of individual instances, each placed separately on different hardware, or even in a different availability zone. It's recommended for critical applications that need to be separated from one another to improve redundancy; unlike a clustered placement group, the goal here is to spread the instances out and keep them as far apart as possible, by placing them on separate racks, to ensure redundancy in case of failure.

A Partitioned placement group combines both approaches: on one hand, instances are separated across different hardware components to maintain redundancy, while on the other hand, several instances are grouped together within a cluster to achieve low latency and high bandwidth.

A few notes: with Partitioned and Spread placement groups you can place instances across different availability zones, but with a Clustered placement group you cannot. Every placement group needs a unique name within your AWS account. Only certain EC2 instance types can be placed inside a Clustered placement group, specifically compute-optimized, GPU, memory-optimized, and storage-optimized instances. AWS recommends putting instances of the same type into the same Clustered placement group. You cannot merge placement groups. You can move an existing instance into a placement group, but before doing so it must be in the stopped state. You can move or delete an instance using the AWS CLI or an AWS SDK, but not through the console.

## High Performance Computing and Data Transfer

High Performance Computing is used by industries such as genomics, finance, machine learning, weather forecasting, and autonomous driving.

There are several ways to bring data into AWS. For terabyte or petabyte scale, you can use Snowball or Snowmobile. For storing data on S3, EFS, or FSx for Windows and similar, you can use AWS DataSync. Direct Connect is a dedicated, private network line from the organization's local infrastructure to AWS; in many cases this can help lower communication costs, increase bandwidth, and provide a more consistent network connection than a regular internet connection.

The compute and networking components that let you implement high performance computing on AWS include GPU- or CPU-optimized EC2 instances, EC2 Fleets using Spot Instances or Spot Fleets, Cluster Placement Groups, enhanced networking, elastic networking, elastic network adapters, and elastic fabric adapters.

On the storage side, instance-attached storage includes EBS, which can scale up to sixty-four thousand IOPS with Provisioned IOPS, and Instance Store, which can scale to millions of IOPS with low latency. Network storage includes Amazon S3, which is a distributed object storage system rather than a file system; Amazon EFS, whose IOPS scaling is based either on total size or on Provisioned IOPS; and Amazon FSx for Lustre, a distributed file system built for high performance computing that uses millions of IOPS and is backed by S3.

On orchestration and automation: AWS Batch lets developers, scientists, and engineers run thousands of batch jobs on AWS; it supports multi-node parallel work and lets you run a single job spread across several EC2 instances, and you can easily schedule scheduled jobs and EC2 instances according to your needs. AWS ParallelCluster is an open-source cluster management tool that lets you manage high performance computing clusters easily on AWS; it uses a simple text file to automatically and securely provision all the resources your high performance computing applications need, and allows automatic creation of the VPC, subnet, cluster type, and instance type.

## AWS WAF

AWS WAF is a web-based application that acts as a firewall, letting you monitor and control HTTP and HTTPS requests being forwarded to Amazon CloudFront, an Application Load Balancer, or API Gateway. You can control incoming requests at three levels: allow all requests except the ones you specify to block, block all requests except the ones you specify to allow, or simply count requests that match characteristics you've specified. For extra protection against internet attacks, you can set conditions that only allow requests matching parameters such as the source IP address, the country of origin, values in request headers, specific strings appearing in requests, request length, blocking likely malicious SQL code, meaning SQL injection, and blocking likely malicious scripts, meaning cross-site scripting. You'd use this feature when you want to block access from malicious IP addresses, and you can also use Network ACLs for that.

## Databases Overview

AWS offers relational databases, known as RDS, the Relational Database Service, which include SQL Server, Oracle, MySQL Server, PostgreSQL, Aurora, and MariaDB; note that for OLTP workloads you'd use RDS. RDS has two central features: multiple availability zones for durability and disaster recovery, and read replicas for improved performance. There's also DynamoDB, a NoSQL database, and Redshift, used for OLAP.

The Aurora and RDS relational database service is essentially Amazon's cloud version of MySQL, which makes it simple to use RDS with existing applications originally written for MySQL. The service includes data backups, snapshots, and very simple replica creation, among other features. RDS is priced similarly to EC2, letting you choose the power of the machine that will run the service, based on the load and performance you need, ranging from a small machine with under two gigabytes of memory up to sixty-eight gigabytes of memory.

## RDS Specifics

RDS runs on virtual machines, but you cannot connect to those underlying virtual machines directly; the connection between RDS and the database is Amazon's responsibility. RDS itself is not serverless, though Aurora is serverless. There are two kinds of backups for RDS: automated backups and database snapshots.

Read Replicas can exist across multiple availability zones, they're used to improve performance, the underlying backups must be active, and they can even live in different regions. They can be MySQL, PostgreSQL, MariaDB, Oracle, or Aurora. You can promote a Read Replica to become the master, but doing so breaks that read replica relationship.

Multi-AZ deployments are used for disaster recovery. You can force a failover from one availability zone to another by rebooting the RDS instance.

## RDS Encryption

Encryption at rest is supported for MySQL, PostgreSQL, SQL Server, MariaDB, Oracle, and Aurora. The encryption itself is performed by Amazon's Key Management Service, KMS. Once an RDS instance is encrypted, all the data stored behind the scenes is encrypted as well, including automated backups, read replicas, and snapshots.

## DynamoDB

DynamoDB data is stored on SSD drives and is distributed across three geographically separated data centers. By default it operates using eventually consistent reads: every write is updated across all copies of the data within one second, and a read performed right after a write should return the most up-to-date data, giving the best read performance. DynamoDB also supports strongly consistent reads, which return the most current result, including all writes made before the current read request, in under one second.

## SimpleDB

SimpleDB is a simple, non-relational database that lets you store and read data through simple means, without the complexity of standard databases. SimpleDB is built on S3 and is known for high speed, scalability, low price, and high durability, since multiple copies of the data are created automatically.

## Redshift

Redshift is a powerful, fast, and inexpensive AWS data warehouse service, used for business intelligence. It operates within a single availability zone only. Redshift can be configured either as a single node with one hundred sixty gigabytes, or in a multi-node configuration consisting of a leader node, which manages client connections and receives queries, and compute nodes, which store data and perform queries and calculations. It can scale up to one hundred twenty-eight nodes.

On backups: the default retention period is one day, with a maximum frequency of thirty-five days. Redshift always tries to keep three copies of your data: the source, a replica on the compute node, and a backup in S3. Redshift can asynchronously replicate your snapshots to S3 in another region for disaster-recovery purposes.

## Aurora

Aurora is Amazon RDS's relational database, compatible with MySQL and PostgreSQL. It performs about five times better than MySQL and three times better than PostgreSQL, at a much lower price, with similar availability. Aurora starts at a size of ten gigabytes and grows in ten-gigabyte increments up to sixty-four terabytes, using an auto-scaling configuration. Its compute components can scale up to thirty-two virtual CPUs and two hundred forty-four gigabytes of RAM.

Aurora can absorb the loss of two copies of its data without impacting write capability, and up to three lost copies without impacting read capability. Aurora has self-healing capability: its blocks and disks are continuously scanned and checked in order to find and automatically correct errors. Two copies of your data live in at least three different availability zones, giving you a total of six copies of your data. You can share Aurora snapshots with other AWS accounts.

There are three types of replicas available: Aurora replicas, up to fifteen; MySQL replicas, up to five; and PostgreSQL replicas, up to one. Automatic failover is available only with Aurora Replicas. Automated backups are active by default, and you can create Aurora snapshots and share them with other AWS accounts. You can use Aurora Serverless if you want a simple, cost-effective solution for infrequent access or unpredictable workloads.

Comparing Aurora Replicas and MySQL Replicas: Aurora supports up to fifteen replicas versus MySQL's five; Aurora replication happens asynchronously within milliseconds versus MySQL's asynchronous replication measured in seconds; Aurora has low performance impact on the primary versus high impact for MySQL; Aurora replicas stay within the region while MySQL replicas can cross regions; Aurora replicas can act as a failover target with no data loss, while MySQL replicas can also act as a failover target but with potential minutes of data loss; Aurora supports automated failover while MySQL does not; Aurora does not support user-defined replication delay while MySQL does; and Aurora does not support different data or schema versus the primary, while MySQL does.

## ElastiCache

ElastiCache is a web service based on caching that improves the performance of web applications in the cloud, by letting them access data quickly and efficiently from a location closer to them, instead of relying on slower disk-based databases. It caches the most common queries and directs users to it to retrieve query results, which provides much faster response speed and reduces load on the primary database by handling part of the query load itself. ElastiCache offers two open-source in-memory caching engines: Memcached and Redis. Redis supports multiple availability zones, and you can back up and restore Redis.

## Database Migration Service

The Database Migration Service, or DMS, lets you perform migrations of RDS, data warehouses, NoSQL databases, and other database types. You can use this feature to transfer data from local, on-premises storage to AWS through AWS Cloud Setup, between two local storage systems, or across a combination of cloud and local storage. If you want to migrate between different source and target database engines, you'll need to use the AWS Schema Conversion Tool, abbreviated SCT.

## Caching Strategies on AWS

Caching is a balance between accurate, up-to-date data on one side and latency on the other. The following services offer caching capability: CloudFront, API Gateway, ElastiCache with Memcached and Redis, and the DynamoDB Accelerator, known as DAX. Generally speaking, the closer to the user the data is stored, the lower the latency will be.

## EMR

EMR stands for Elastic MapReduce, a feature used for processing big data. It's made up of a master node, a core node, and optionally task nodes. By default, logs are stored on the master node. You can configure replication of all the logs on the master node to S3 at five-minute intervals, but this setting can only be configured the first time you create the cluster.

## Advanced IAM: AWS Directory Service

AWS Directory Service is a family of managed services. It connects AWS resources with an on-premises Active Directory, and it also offers a standalone identity management service in the cloud that uses existing credentials. You can perform single sign-on to any domain-joined EC2 instance. The services that support Active Directory are AWS Managed Microsoft AD, AD Connector, and Simple AD; the services that don't support Active Directory are Cloud Directory and Cognito user pools.

Active Directory itself is a Windows management service for on-premises environments, with a hierarchical database of users, groups, and computers organized as trees and forests. It includes group policy, LDAP and DNS, Kerberos, LDAP, and NTLM authentication, and it's highly available.

AWS Managed Microsoft AD runs Active Directory domain controllers on Windows servers. Applications within a VPC can reach it, you can add additional domain controllers to improve performance and high availability, and it offers exclusive access to the domain controllers. You can extend an existing on-premises Active Directory using an AD Trust relationship.

Simple AD is a standalone management service with basic Active Directory capabilities. It's suited for businesses ranging from small, under five hundred employees, up to five thousand employees, it makes EC2 easier to manage, and it's suited for Linux workloads that need LDAP. It does not support trust relationships and cannot be joined to an on-premises Active Directory.

## Evaluating IAM Policies

Anything not explicitly stated as granted permission means there's no permission for it. If a policy explicitly denies permission for a certain action, that denial is stronger than any other permission granting access to that same forbidden action. Only attached policies have any effect. An Amazon Resource Name, abbreviated ARN, is a template made up of several parts representing a specific AWS resource, built in the form: arn, partition, service, region, account ID, followed by the resource itself. AWS aggregates all the policies that apply, and there's a division of responsibility between Amazon's responsibilities and the customer's responsibilities. On Amazon's side, that includes things like multi-availability-zone deployment, patching, monitoring, and recovery, instance rotation, and snapshotting and restoring. On the customer's side, that includes users, groups, and group policy objects, standard Active Directory tools, scaling out domain controllers, trusts through resource forests, certificate authorities using LDAPS, and federation.

## Permission Boundaries, Resource Access Manager, and Single Sign-On

Permission Boundaries are used to centralize management of other users. They prevent privilege escalation or granting of unnecessary permissions, and they control the maximum amount of permission that an IAM policy can grant. Typical use cases include developers creating roles for Lambda functions, application developers creating roles for EC2 instances, and administrators creating ad hoc users.

The AWS Resource Access Manager, or RAM, is used to share AWS resources between different accounts. Currently, only certain resource types can be shared this way, including App Mesh, Aurora, CodeBuild, EC2, EC2 Image Builder, License Manager, Resource Groups, and Route 53.

AWS Single Sign-On is a service that centralizes and manages access to your AWS account and to other business applications, and it integrates with SAML and with Active Directory.

## DNS Basics

The Domain Name System, or DNS, is a tool responsible for translating internet addresses, meaning domain names, into IP addresses whenever a record is accessed. Elastic Load Balancers don't have predefined IPv4 addresses, so you must always address them using DNS.

An Alias Record is used to point us from a certain DNS record to one of the following: Elastic Load Balancers, CloudFront distributions, or S3 buckets. A CNAME, short for Canonical Name, is used to point us from one DNS record to another, for example redirecting a mobile-phone visitor to a different address suited to a mobile-optimized site. Note that you should always prefer an Alias Record over a CNAME.

TTL, short for Time to Live, is the amount of time, in seconds, that a DNS record is stored in cache; the shorter that time is, the faster changes made in DNS take effect. SOA records store the following information: the name of the server that supplied the information for the zone, the administrator of the zone, the current version of the zone file, and the default number of seconds for the TTL field on resource records.

NS Records, short for Name Server Records, are used by top-level-domain servers to direct requests to the DNS server holding the authoritative DNS records. A Records, short for Address Records, are used to translate a domain name into an IP address. There are two more DNS record types worth knowing: MX Records and PTR Records.

## Registering a Domain and Route 53 Routing Policies

You can purchase a domain name directly through AWS. Registering a domain can take up to three days depending on the circumstances.

A Simple Routing Policy is used to route a DNS record to several predefined IP addresses, and routing to those addresses happens in random order. A Multivalue Answer Routing policy is similar to the Simple policy, routing a DNS record to several predefined values such as IP addresses, again in random order, but unlike the Simple policy, it performs a health check on each resource before routing traffic to it, so Route 53 will only return values for healthy resources.

A Weighted Routing Policy lets you split traffic reaching your DNS record based on assigned weights; for example, you could route ten percent of traffic to one availability zone and ninety percent to another.

On Health Checks: you can define health checks on individual records. If a record fails its health check, it's removed from Route 53 until it passes the check successfully again. You can configure an SNS notification to alert you if a health check fails.

Latency-Based Routing lets you route traffic reaching your DNS record to the availability zone that will give the user the lowest latency.

A Failover Routing Policy lets you work in an active-passive configuration, for example routing all traffic to a primary site in one availability zone and a secondary site in another. Route 53 monitors the health of the primary site through a health check, and once that health check detects the primary site is down, it performs a failover and routes all traffic to the secondary site.

A Geolocation Routing Policy lets you route traffic reaching your DNS record to the availability zone closest to the user's geographic location; for example, you could route all requests coming from Europe to a site tailored to a European audience in terms of pricing, language, and so on.

Geoproximity Routing, available only through Traffic Flow, lets you route traffic reaching your DNS record to an availability zone based on both the user's geographic location and the geographic location of the availability zone where your AWS resources reside. To use this method, you must use Route 53 Traffic Flow.

## VPC Basics

A VPC is a logical data center inside AWS. It's made up of internet gateways or virtual private gateways, route tables, Network Access Control Lists, which are stateless, and Security Groups, which are stateful. One subnet equals one availability zone.

With a VPC you can run instances inside a subnet of your choosing, assign an IP address range to each subnet, define route tables between subnets, create an internet gateway and attach it to your VPC, get better control over the security of your AWS resources, use security groups on instances, and use subnet-level Network Access Control Lists, abbreviated ACLs.

What's the difference between a Default VPC and a Custom VPC? A Default VPC is user-friendly and lets you launch instances immediately. Every subnet in a Default VPC has outbound internet access. Every EC2 instance gets both a public IP address and a private IP address.

## VPC Peering

VPC Peering lets you connect one VPC to another using a direct network route through private IP addresses. Note that this only supports connecting VPCs located in the same region. The instances behave as if they're on the same private network. You can peer a VPC with another VPC belonging to a different AWS user, or the same one. Peering connections form a star shape, with one central VPC connected to up to four others. There's no support for transitive peering, meaning you cannot connect two VPCs through a central VPC; to connect one VPC to another you need to create a direct connection rather than routing through another VPC.

## Creating a New VPC

When you create a new VPC, a Route Table, a Network Access Control List, and a Security Group are all created automatically in a default configuration. However, a Subnet or Internet Gateway is not created automatically. Note that Availability Zone us-east-1a in your AWS account could be a completely different physical availability zone from us-east-1a in a different account, since availability zones are distributed randomly. Amazon always reserves five IP addresses in each of your subnets. You can only have one Internet Gateway per VPC, and you cannot attach two VPCs to a single Security Group.

## NAT Instances and NAT Gateways

For NAT Instances: when creating a NAT instance, you need to disable the source and destination check on the instance. A NAT instance must be placed in a public subnet. You need to define a route from the private subnet to the NAT instance for it to work. The amount of traffic a NAT instance can handle depends on the instance size, so if there's a bottleneck, you need to increase the instance size. You can achieve high availability by using Auto Scaling Groups, multiple subnets across different availability zones, and a script to perform automatic failover. You should also place the NAT instance behind a Security Group.

NAT Gateways offer built-in redundancy within their availability zone, and they're the preferred choice in the industry. They start at five gigabits per second of throughput and currently scale up to forty-five gigabits per second. They require no patching, and they're not associated with security groups. A public IP address is automatically assigned. Remember that you'll need to update the route table, but you don't need to disable the source and destination checks. Note that if you have multiple resources across several availability zones sharing a single NAT Gateway, and the availability zone containing that NAT Gateway fails, resources in the other availability zones will lose internet access. To build an architecture where each availability zone is independent, you should create a NAT Gateway in every availability zone and configure the route tables so that resources use the NAT Gateway in their own availability zone.

## Network ACLs versus Security Groups

When you create a VPC, it automatically comes with a default Network ACL that, by default, allows all inbound and outbound traffic. You can create a custom Network ACL, and by default, every custom Network ACL denies all inbound and outbound traffic until you add rules. Every subnet in a VPC must be associated with a Network ACL. If you don't associate a specific subnet with a Network ACL, that subnet gets automatically associated with the Default Network ACL. You should use a Network ACL to block specific IP addresses, not a Security Group. You can associate a Network ACL with multiple subnets, though each subnet can only be associated with one Network ACL at any given moment, and associating a Network ACL with a subnet removes the previous association. A Network ACL contains a numbered list of rules processed in order, starting from the lowest-numbered rule; the order matters critically, because a rule with a lower number takes precedence over one appearing later in the list. Network ACLs have separate rules for inbound and outbound traffic, and each rule can either allow or deny traffic. Network ACLs are stateless, meaning that for every rule allowing traffic in, you need to define a corresponding rule denying traffic in the opposite direction, and vice versa; these rules are not created automatically.

## VPC Flow Logs

VPC Flow Logs let you save logs of all traffic passing through a VPC. You cannot enable Flow Logs for a VPC connected to your own VPC through Peering, unless they belong to the same AWS account. You can add tags to Flow Logs. Once a Flow Log has been created, you cannot change its settings, for example you can't reassign it a different IAM role. Not all IP traffic is monitored; for example, traffic generated by instances connecting to Amazon's own DNS server isn't monitored, although if you use your own DNS server, that traffic will be monitored. Traffic generated by Windows instances for Amazon Windows license activation is not monitored. Traffic to and from the metadata address one-six-nine-dot-two-five-four-dot-one-six-nine-dot-two-five-four for instance metadata is not monitored, nor is DHCP traffic, nor traffic to the IP addresses reserved for the default VPC router.

## Bastion Hosts

A Bastion Host is a virtual server with strong security, stripped of all unnecessary software to minimize potential risk. It's used to relay traffic between an internet gateway and a private subnet. A NAT Instance or NAT Gateway is used to give internet access to EC2 instances in private subnets, whereas a Bastion is used to securely manage EC2 instances, via SSH for Linux and RDP for Windows. You need to define a public subnet or an Elastic IP for it. In Australia, a Bastion is sometimes called a Jump Box. You cannot use a NAT Gateway as a Bastion.

## Direct Connect

Direct Connect is a dedicated, private network line from the organization's local infrastructure, on-premises, to AWS. In many cases this can help lower communication costs, increase bandwidth, and provide a more consistent network connection than a regular internet connection. This feature connects your data center directly to AWS's services, and it's used in environments with heavy network traffic, or in cases where you need a reliable and secure connection to AWS.

The steps to set up Direct Connect are as follows: create a virtual interface in the Direct Connect console, which is a public virtual interface; go to the VPC console and then to VPN connections, and create a customer gateway; create a virtual private gateway; attach the virtual private gateway to the desired VPC; select VPN connections and create a new VPN connection; select the virtual private gateway and the customer gateway; and once the VPN is available, set up the VPN on the customer gateway or firewall.

## AWS Global Accelerator and VPC Endpoints

AWS Global Accelerator lets you create accelerators to improve availability and performance for your applications, for both local and global users. Two static IP addresses are assigned automatically, or alternatively you can configure your own addresses. You can control traffic using traffic dials, done through endpoint groups.

VPC Endpoints let you privately connect your VPC to a range of supported AWS services and to services offered through AWS PrivateLink, without needing an internet gateway, a NAT device, a VPN connection, or AWS Direct Connect. Instances inside a VPC don't need a public IP address to communicate with resources through this feature, and traffic between your VPC and other services never leaves Amazon's network. Endpoints are virtual devices; you can scale them out or scale them horizontally, and they offer redundancy and high availability. They let the instances in your VPC and supported services avoid being exposed to availability risks or bandwidth restrictions in your network traffic. There are two types of VPC Endpoints: Interface Endpoints and Gateway Endpoints. The services currently supported through Gateway Endpoints are Amazon S3 and DynamoDB.

## AWS PrivateLink

AWS PrivateLink lets you connect your own VPC to tens, hundreds, or even thousands of customer VPCs. It doesn't require VPC peering, route tables, NAT, internet gateways, or the like. It requires a Network Load Balancer on the service VPC's side and an Elastic Network Interface on the customer VPC's side.

## AWS Transit Gateway

AWS Transit Gateway lets you perform transitive peering across thousands of VPCs and on-premises data centers. It works in a hub-and-spoke model. It operates on a regional basis, though you can use it across multiple regions. It can be used across different AWS accounts through the Resource Access Manager. You can use route tables to restrict how one VPC can communicate with another. It works with both Direct Connect and VPN connections. It supports IP Multicast, which no other AWS service supports.

## AWS VPN CloudHub

AWS VPN CloudHub lets you manage multiple sites, each with its own VPN connection, and you can use this feature to connect all those sites together. It works in a hub-and-spoke model, it's cheap and easy to manage, and it operates over the public internet, but all traffic between the customer's gateway and AWS's gateway is encrypted.

## AWS Network Costs

You should always prefer using private IP addresses over public IP addresses to save on costs, since this uses AWS's own backbone network. If you want to cut networking costs entirely, group all your EC2 instances into the same availability zone and use private IP addresses; this approach costs nothing, but it creates a single point of failure.

## Steps to Create a VPC, Summarized

Create the VPC. Note that when you create a custom VPC, Network ACLs, a Security Group, and a Route Table are all created automatically. Create an internet gateway and connect that internet gateway to the VPC. Create a public subnet and a private subnet in different availability zones. Create two route tables and associate each one with its matching subnet. Create two Network ACLs and associate each one with its matching subnet. Configure inbound and outbound rules for each of the Network ACLs.

## Load Balancers

There are three types of load balancer. The Application Load Balancer is designed to balance traffic for HTTP and HTTPS protocols, operates at layer seven of the seven-layer networking model, and is intelligent, capable of routing requests to specific web servers.

The Network Load Balancer is designed to balance TCP traffic, operates at layer four of the seven-layer model, and can process millions of requests per second while keeping latency very low; it's used for especially high-performance needs.

The Classic Load Balancer is designed to balance traffic for applications running over HTTP or HTTPS. It also supports layer-seven features like X-Forwarded-For, used when you need to know the IP addresses of the users hitting your application, along with sticky sessions. It can also work at layer four for applications that only run over TCP. It's less intelligent than the Application Load Balancer, but it's the cheapest option. Note that when the application stops responding, the Classic Load Balancer, meaning the ELB, responds with a five-oh-four error; that error indicates a problem in the application, not in the load balancer, and the underlying issue could be in the database or the web server.

Instances monitored by a load balancer can be in one of two states: InService or OutOfService. Health checks verify an instance's health by communicating with it directly. Load balancers have their own DNS address; you never get a load balancer's IP address directly.

Sticky Sessions is a feature that lets a user remain connected to the same EC2 instance, which can be useful in cases where you're storing information locally on that particular instance. Cross-Zone Load Balancing lets you balance traffic across different availability zones. Path Pattern lets you route traffic to different EC2 instances based on the URL within the request.

## Auto Scaling

Auto Scaling has three components. Groups are the logical component, which could be a group of web servers, a group of databases, and so on. Launch Configuration Templates are used by groups to create EC2 instances, and you can specify information such as the AMI ID, instance type, key pair, and security group as part of these templates. Scaling Options let you perform scaling in various ways to fit different needs.

There are several approaches to scaling. You can maintain a predefined number of instances at all times; for example, you might define a desired count of ten instances, and any time a health check finds unhealthy instances, they get terminated and replaced with new ones. You can perform manual scaling, increasing or decreasing the number of running instances whenever you want. You can perform scheduled scaling, defining in advance a date and time when you want to change the number of running instances, which is useful if you know certain times bring heavier load and need more running instances, or conversely, quieter hours, such as overnight or on weekends, when you can reduce the instance count and save on costs. You can perform on-demand scaling, defining parameters in advance by which the instance count changes, for example deciding that once CPU usage reaches fifty percent, you'll increase the instance count to handle the load. And you can perform predictive scaling: you can use Amazon EC2 Auto Scaling combined with AWS Auto Scaling to scale across several resources at once, based on prior usage data and predictions of the actions that will be needed.

## CloudFormation, Elastic Beanstalk, OpsWorks, Glue, and Trusted Advisor

CloudFormation is a feature that lets you manage your entire AWS environment through scripting. Quickstart includes a number of prebuilt CloudFormation templates, created by AWS Solutions Architects, that let you build complex environments quickly.

Elastic Beanstalk lets you deploy and manage applications on AWS quickly, without having to worry about the underlying infrastructure those applications run on. You simply upload your application, and Elastic Beanstalk automatically handles all the details for you, including capacity provisioning, load balancing, scaling, and application health monitoring.

AWS OpsWorks is a configuration management service that provides managed instances of Puppet and Chef, which are automation platforms that let you use code to automate the configuration of your servers. OpsWorks lets you use Chef and Puppet to automate how your instances are configured, managed, and launched, both in AWS and in your on-premises environment. OpsWorks comes in three offerings: AWS OpsWorks for Chef Automate, AWS OpsWorks for Puppet Enterprise, and AWS OpsWorks Stacks.

AWS Glue is a fully managed extract, transform, and load service, abbreviated ETL, that makes it easy for customers to prepare and load their data for analytics.

AWS Trusted Advisor is an online tool that gives you real-time guidance to help you provision your resources according to AWS best practices. It checks your AWS environment and offers recommendations for saving money, improving system performance and reliability, or closing security gaps.

## High Availability with Bastion Hosts

There are two configurations for achieving high availability with Bastion Hosts. The first option: two Bastion Host servers across two different availability zones, using a Network Load Balancer with a static IP address, performing health checks in order to fail over from one server to the other when needed. Note that you cannot use an Application Load Balancer here, because it operates at layer seven, and here you need layer four.

The second option: a single Bastion Host in one availability zone, sitting behind an Auto Scaling Group with health checks and an Elastic IP address. If the server crashes, the health check fails and the Auto Scaling Group provisions a new EC2 instance in a separate availability zone. You can use a user-data script to reassign the same Elastic IP address to the new server. This is the cheapest option, but it does not provide one hundred percent fault tolerance.

## On-Premises Migration Strategies with AWS

The Database Migration Service lets you migrate RDS, data warehouses, NoSQL databases, and other database types. The Server Migration Service supports incremental replication of servers from your local, on-premises environment to AWS; it can be used as a backup tool, for multi-site strategy, and as a disaster-recovery tool.

The AWS Application Discovery Service lets enterprise customers plan migration projects by gathering information about their on-premises environment. You install the agent as a virtual appliance on vCenter; the tool then builds a map of your entire on-premises environment along with all its dependencies. That information is stored in encrypted form in the AWS Application Discovery Service data store, and you can export it to a CSV file to use for a total-cost-of-ownership estimate, letting you see how much it would cost to move your local environment to AWS. This information is also available in the AWS Migration Hub, where you can perform migration to discovered servers and track their progress throughout the migration to AWS.

VM Import and Export lets you migrate existing applications onto EC2. You can use it to implement a disaster-recovery strategy on AWS or to use AWS as a secondary site. You can also use it to export virtual machines running on AWS back to your on-premises environment. You can also download Amazon Linux 2 as an ISO image and use it with any of the leading virtualization providers, such as VMware, Hyper-V, KVM, or VirtualBox.

## Amazon SQS

SQS is an AWS web service that lets you store messages in a queue while they wait for a server to finish processing them. Using SQS lets you decouple the different components of your applications so they can run independently, which makes it easier to manage messages between all the components. Every application component can store messages in the queue and pull them out using the SQS API. SQS is pull-based rather than push-based. Stored messages can be up to two hundred fifty-six kilobytes in size; if they're larger than that, they get stored in S3 instead of SQS. Messages can remain in the queue anywhere from one minute up to fourteen days, with a default retention period of four days.

SQS offers two types of queues to choose from. The Standard queue can process a nearly unlimited number of requests per second, and it guarantees that every message is delivered at least once. It's possible for more than one copy of a message to be sent, but it does guarantee that messages arrive in the same order they were sent.

The FIFO queue, short for First In First Out, has as its central feature that every message is sent exactly once, and a message that arrives first is sent first. This queue keeps exactly one copy of every message to prevent duplicates. Every message remains available until it's been processed and deleted by the component that handled it. Message grouping is also supported, so you can store several message groups in a single queue. FIFO queues are limited to three hundred transactions per second, but otherwise have all the same capabilities as a standard queue.

Visibility Timeout is the amount of time a message stays invisible in the queue after a reader pulls it out. The message needs to be processed before the allotted timeout expires; after that, if it was processed, it gets deleted from the queue. If the message wasn't processed in time, it becomes visible again, and a different reader will handle it. This situation can cause a given message to be sent twice. To handle a situation where messages get sent twice, you should increase the visibility timeout. The maximum visibility timeout is twelve hours.

SQS Long Polling is a way to save on costs when retrieving messages from a queue. While the regular approach, short polling, returns a result immediately, even if the queue is empty, long polling doesn't return a result until a message arrives in the queue or the timeout expires. Every check of the queue for messages incurs a charge for that action, so you want to use long polling to avoid making unnecessary checks that would generate needless charges.

## Simple Workflow Service

SWF is a web-based service that lets you easily coordinate work across several different application components. SWF lets you build applications for a variety of uses, such as data processing, managing the backend of web applications, business process management, and more. Every task, called a domain, represents a number of tasks in the application, which can be carried out by running code, calling web servers, human actions, and scripts.

There are three types of SWF actors. Workflow Starters are applications that can start a workflow sequence; for example, this could be a shopping website when someone places an order, or a mobile app checking bus schedules. Deciders control the flow of tasks to be performed; if a task finishes, or fails, the decider decides what to do next. Activity Workers carry out and execute the tasks themselves.

## Amazon SNS

SNS is a web-based service that makes it easy to set up, manage, and send notifications from the cloud. It gives developers a tool with extensibility, flexibility, and good price-to-value ratio, for sending messages from applications and delivering them immediately to subscribers or to other applications. You can send notifications to major providers including Apple, Google, Fire OS, Windows, and Android devices in China only. You can also send SMS text messages, emails, messages to SQS queues, or to any HTTP endpoint. It delivers messages immediately, with no polling required. It offers simple APIs and simple integration with other applications. It supports flexible message delivery across multiple transport protocols. It's inexpensive, working on a pay-as-you-go model with no upfront payment. It can be managed easily through the AWS Console and offers the simplicity of a point-and-click interface.

What's the difference between SWF and SQS? Both are AWS messaging services. SNS works in a push model, while SQS works in a pull or polling model. SQS has a retention period of up to fourteen days, whereas in SWF, a workflow sequence can persist for an entire year. SWF represents a task-oriented API, whereas SQS gives us a message-oriented API. SWF guarantees that a task will be executed exactly once and never duplicated, whereas with SQS you have to handle duplicate messages yourself and make sure a message gets processed only once. SWF tracks the execution of all tasks and events in the application, whereas with SQS you have to track execution yourself.

## Elastic Transcoder and API Gateway

Elastic Transcoder is a cloud-based media conversion service. It converts media files from their original format into other formats that will work on smartphones, tablets, personal computers, and so on. It provides conversion to the most popular formats. Billing is based on the length of the video you're converting, in minutes, and on the resolution you're converting to.

API Gateway is a fully managed service that lets developers publish, maintain, monitor, and secure APIs at any scale; you can think of it as a doorway into your AWS environment. API Gateway offers caching capability to boost performance. API Gateway has a low price and performs scaling automatically. You can apply throttling to API Gateway to prevent attacks. You can expose an HTTPS endpoint in order to define a RESTful API. You can connect it to services like Lambda and DynamoDB. You can send any API endpoint to a different target. You can scale it easily. You can monitor and control usage through an API key. You can maintain multiple versions of your API. You can save logs of the results to CloudWatch.

CORS is a mechanism that allows sending requests from one domain to restricted resources on a web page belonging to a different domain. If you're using AJAX or JavaScript that works across multiple domains together with API Gateway, you need to make sure you've enabled CORS on API Gateway. CORS is maintained on the client side.

## Amazon Kinesis

Streaming data is data that's generated continuously by thousands of data sources, which typically send their data records simultaneously and in small pieces, on the order of kilobytes. Examples include purchases from online stores, stock market activity, in-game data during gameplay, social media data, geospatial data, and data from IoT sensors. Kinesis is an AWS platform used to send your streaming data to other resources as needed. You can load and analyze streaming data and use it to build custom applications tailored to your business needs.

There are three types of Kinesis. Kinesis Streams stores data for between twenty-four hours and seven days, and that data can come from a variety of sources, such as a mobile device performing actions in some application, an IoT farm, an EC2 instance, or a personal computer performing some action; the data is transferred into Kinesis Streams and stored in shards, with a distinct shard for each different type of data. Afterward the data is passed to an EC2 instance, where the required processing on the data is performed. Finally, the data is stored in various places depending on need, for example DynamoDB, S3, EMR, or Redshift.

Kinesis Firehose receives data from a variety of sources, similar to Kinesis Streams, and then transfers it to Firehose, which has no persistent storage, meaning the data must be processed the moment it arrives. You can define a Lambda function that runs automatically whenever new data arrives. After the required processing, the data is transferred to S3, and from there it can optionally be moved on to Redshift, or alternatively, you can choose to store the data in an Elasticsearch cluster.

Kinesis Analytics works with both Kinesis Streams and Kinesis Firehose, and it has the ability to process data on the fly within either of these services, and then store the data afterward in S3, Redshift, or an Elasticsearch cluster.

## Web Identity Federation and Cognito

Web Identity Federation lets users access AWS resources after they've successfully authenticated through a web service like Amazon, Facebook, or Google. After a successful login, they receive an authentication code from the Web ID Provider, which they can exchange for temporary AWS credentials and an IAM role.

This feature also lets you do the following: let users sign up and log into your applications; allow guest-user access; act as an identity broker between your applications and the Web ID Provider, so you don't have to write any extra code yourself; synchronize user data across multiple devices; and it's recommended for all mobile applications using AWS services. A User Pool is responsible for user registration, authentication, and account recovery. Identity Pools are responsible for authorizing access to your AWS resources.

## Event Processing Patterns

This working pattern lets us pass messages between the different components of an application asynchronously. It's made up of a Topic, which is the subject of the message; a Publisher, which broadcasts the message; and a Subscriber, which receives the message.

Two important terms here are Event-Driven Architecture and the Dead-Letter Queue. Several AWS resources work using this pattern. With SNS, messages published to a topic that fail to be sent to their destination are sent to an SQS queue, and they remain there for further analysis or reprocessing. With SQS, messages sent to a queue that exceed the maximum number of receives that queue can handle, known as maxReceiveCount, get moved to a dead-letter queue, which is essentially just another SQS queue. With Lambda, results from asynchronous calls that fail get resent and delivered to an SQS queue or an SNS topic.

The Fanout Pattern: instead of sending messages directly to their destination, which would give us no visibility into whether the messages were successfully sent or not, we send them to an SNS topic, and from there it forwards them to their destination in an organized way.

S3 Event Notifications: you can configure automatic message sending for a number of actions that happen in S3, namely Object Created, Object Removed, Object Restored, Reduced Redundancy Storage Object Lost, and Replication. You can add filters and send these notifications to the following services: an SQS queue, an SNS topic, or a Lambda function. Note that you need to enable versioning to make sure the notifications get delivered.

## Security: KMS

KMS is a security and key-management service that handles encryption and decryption for every region. It manages your Customer Master Keys. It's ideal for S3 objects, database passwords, and API keys stored in Systems Manager Parameter Store. It can encrypt and decrypt data up to four kilobytes in size. It integrates with most AWS services. You're billed per API call. It offers audit capability using CloudTrail, sending logs to S3. It operates under FIPS 140-2 Level 2 compliance.

There are two types of Customer Master Keys, abbreviated CMKs. Symmetric keys use the same key for both encryption and decryption. They work using the AES-256 encryption protocol. The key never leaves AWS in an unencrypted form. You must make a KMS API call to use this key. AWS services that integrate with KMS use symmetric CMKs. They can encrypt, decrypt, and re-encrypt data, and they can generate data keys, data key pairs, and random byte strings.

Asymmetric keys have a private key and a public key that are mathematically linked. They support RSA and Elliptic-Curve Cryptography. The private key never leaves AWS unencrypted. You must make a KMS API call to use the private key. You can download the public key and use it outside of AWS. It can be used outside AWS by users who cannot make KMS API calls themselves. AWS services that integrate with KMS do not support asymmetric CMKs. They support signed messages and signature verification.

There are three types of CMKs overall. Customer Managed keys let you rotate the keys yourself, they're controlled by key policies, and you can turn them on and off. AWS Managed CMKs are free, and they're the default choice when you select encryption in most AWS services, and only that specific service can use them directly. AWS Owned CMKs are used by AWS jointly across many accounts, and you don't typically encounter this option in practice.

## CloudHSM

CloudHSM is a dedicated hardware security module. It operates under FIPS 140-2 Level 3 compliance, compared to KMS, which operates at Level 2. It manages only your keys, not passwords. It has no access to your other managed AWS resources. It runs inside a VPC in your own account. It's single-tenant, uses dedicated hardware, and has a cluster that can span multiple availability zones. It works using industry-standard APIs rather than AWS's own APIs. It meets regulatory compliance requirements. It works with the following standards: PKCS eleven, Java Cryptography Extensions, and Microsoft CryptoNG. You need to keep your keys somewhere safe, since they cannot be recovered if lost.

## Systems Manager Parameter Store and Secrets Manager

Systems Manager Parameter Store is a component of AWS Systems Manager, or SSM. It provides secure, serverless storage for configuration values and secrets, and you can store things like passwords, database connection details, license keys, and API keys inside it. You can store values in encrypted form using KMS, or as plain text. It separates data from source control. It stores values hierarchically. It tracks versions. You can set a time-to-live so that certain values, like passwords, expire.

Secrets Manager is a feature similar to Systems Manager Parameter Store. It charges per secret stored and per ten thousand API calls. It performs rotation of stored secrets, meaning it automatically changes passwords for you. It applies the new password or key to RDS on your behalf. It automatically generates random secrets.

## AWS Shield

AWS Shield is a feature that provides protection against distributed denial-of-service attacks, known as DDoS attacks. There are two tiers of protection. AWS Shield Standard applies automatically to all customers at no charge, and it protects against common attacks at layers three and four of the OSI model, such as SYN or UDP floods and reflection attacks; it stopped a two-point-three-terabit-per-second DDoS attack over three days back in February of 2020. AWS Shield Advanced costs three thousand dollars per month per organization, and it provides enhanced protection for Global Accelerator, CloudFront, Elastic Load Balancing, EC2, and Route 53. It offers support for business and enterprise customers, providing them round-the-clock access to a DDoS response team, and it provides protection against incurring high costs as a result of a DDoS attack.

## WAF, Revisited

WAF is a firewall based on web applications, standing for Web Application Firewall, that lets you monitor HTTP and HTTPS requests being forwarded to CloudFront, an Application Load Balancer, or API Gateway. It gives you control over access to content. You configure filtering rules to allow or deny traffic based on IP addresses, parameters within the URL, and SQL query injection detection. Blocked traffic returns an HTTP 403 Forbidden error.

## Serverless: AWS Lambda

AWS Lambda is a compute service that lets you upload your own code and turn it into a Lambda function. The Lambda function handles everything related to provisioning and managing the servers behind the scenes that run your code. You don't need to worry about operating systems, scaling, patching, and so on. Lambda scales out automatically. A Lambda function is self-contained: one event equals one function. A Lambda function can trigger another Lambda function, so a single event can effectively translate into many functions running, if those functions keep triggering one another. Lambda is serverless.

In complex architectures, you can use AWS X-Ray to perform debugging and better understand what's happening. Lambda can perform actions globally; for example, you could use it to back up files from one S3 bucket to another. The maximum run time for a Lambda function is nine hundred seconds, which equals fifteen minutes.

You can use Lambda in the following ways: as a compute service that gets triggered and runs your code in response to a particular event, an event-driven model, where those events could be data changes in S3 or in DynamoDB; or as a compute service that gets triggered and runs your code in response to an HTTP request, through Amazon API Gateway, or through API calls using an SDK.

Lambda supports the following languages: Node.js, Java, Python, C sharp, Go, and PowerShell.

Lambda pricing works like this: the first million requests each month are free, after which the price is twenty cents per one million requests. The duration charge is calculated from when your code starts running until it returns a value or terminates, rounded up to the nearest one hundred milliseconds. The price also depends on how much memory you've allocated to your function. You're billed at a rate of point-zero-zero-zero-zero-one-six-six-seven dollars per gigabyte-second.

AWS services that can trigger a Lambda function include Alexa Skills, Cognito, an IoT Rule, SNS, Kinesis, SQS, S3, DynamoDB, EventBridge, CloudWatch, and API Gateway.

## SAM

SAM stands for Serverless Application Model, and it's an extension of CloudFormation, optimized for serverless applications. It supports new resource types, such as functions, APIs, and tables. It supports everything CloudFormation supports. It lets you run serverless applications locally.

## ECS

ECS stands for Elastic Container Service. It's an orchestration service for managing containers. You can create clusters to manage fleets of containers. You can manage EC2 instances or Fargate instances. You can schedule containers. You can define rules for CPU and memory requirements. You can monitor resource usage. You can perform updates, deployments, and rollbacks. It's free to use. It works with VPC, security groups, and EBS volumes. It works with Elastic Load Balancing. It works with CloudTrail and CloudFormation.

The components of ECS are as follows. A Cluster is a logical collection of ECS resources, which can be EC2 ECS instances or Fargate instances. A Task Definition defines your application; it's similar to a Dockerfile but for running containers in ECS, and it can contain multiple containers. A Container Definition sits inside a Task Definition, and its job is to define the containers the task uses, controlling CPU and memory allocation and port management. A Task is a single running copy, an instance, of each container defined by the Task Definition; it's a running, working copy of the application. A Service lets you scale a Task Definition by adding tasks, and it sets minimum and maximum values. A Registry functions as storage for container images, used for downloading images to create containers.

Regarding ECS security architecture: applying a policy at the EC2 instance role level applies that policy to every task running on that EC2 instance, whereas applying a policy at the task role level applies the policy per individual task, for example allowing one role access only to S3, another role access to both S3 and DynamoDB, and a third role access only to DynamoDB.

## Docker and Containers

A container is a package that bundles applications, libraries, runtime files, and any other tools needed, meaning dependencies, in order to run the application. It runs on a container engine such as Docker. It offers the isolation benefits of virtualization with much less overhead, and it starts up much faster than virtual machines. Containerized applications are portable and provide a consistent environment.

## Fargate, EKS, and ECR

Fargate functions as a serverless container engine. With it, you don't need to provision or manage servers yourself. Billing happens per application rather than per resource. It works with both ECS and EKS. Every workload runs with its own kernel. It provides isolation and security. You'd choose to use EC2 instead of Fargate in cases involving regulatory requirements, a need for custom configuration, or a need for GPUs.

EKS stands for Elastic Kubernetes Service. Kubernetes is open-source software that lets you deploy and manage containerized applications at scale. The way you use it is identical whether you're on-premises or in the cloud. Containers are grouped together in pods. Like ECS, EKS supports both EC2 and Fargate. You might choose EKS if you're already using Kubernetes, or if you want to migrate to AWS.

ECR stands for Elastic Container Registry. It's a service that manages your Docker container registry. It stores, manages, and deploys images. It works with both ECS and EKS. It works with on-premises deployments as well. It offers high availability. It integrates with IAM. Billing is based on storage and data transfer usage.

Regarding ECS's integration with Elastic Load Balancing: it distributes traffic evenly across all the tasks in a service. It supports the Application Load Balancer, the Network Load Balancer, and the Classic Load Balancer. It uses an Application Load Balancer to route HTTP and HTTPS traffic at layer seven. It uses a Network Load Balancer or a Classic Load Balancer to route TCP traffic at layer four. It's supported both through EC2 launch types and through Fargate launch types. Using an Application Load Balancer allows dynamic host port mapping, path-based routing, and the use of priority rules. Whenever possible, you should always prefer using an Application Load Balancer over a Network or Classic Load Balancer.

*End of notes.*

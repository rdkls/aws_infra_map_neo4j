# AWS Infra Map
Load your AWS environment into neo4j db

Example usage:

```
docker run
    -d \
    --name aws_map_myaccount \
    --env NEO4J_AUTH=$NEO4J_AUTH \
    --env AWS_TO_NEO4J_LIMIT_REGION=ap-southeast-2  \
    --env AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    --env AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    --env AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
    -p 80:7474 \
    -p 7687:7687 \
    aws_infra_map
```


# Environment Variables
| Name | Format | Example | Purpose
|-|-|
| NEO4J_AUTH | user/pass | neo4j/happyjoe4u | Sets initial admin creds for neo4j
| AWS_DEFAULT_REGION | string | us-east-1 | DEFAULT AWS region  (note if AWS_TO_NEO4J_LIMIT_REGION is not set all regions will still be scanned)
| AWS_TO_NEO4J_LIMIT_REGION | string | us-east-1 | LIMIT to one AWS region (default is all)

The rest AWS_* are standard AWS auth credentials, used by awless to pull your config data
Note only read permissions are necessary (and recommended)

NEO4J_AUTH has format user/pass
and sets initial admin creds for neo4j

# Results
![Subnet AZs](./doc/img/subnet-zone-regions.png)
![SNS Subscriptions](./doc/img/sns-topics.png)
![Instances](./doc/img/instances-network.png)
# Example run

```
mbp:~ nick - mocorp$ docker run -d     --name aws_mocorp_infra_map     --env AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY     --env AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID     --env AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN          --env NEO4J_AUTH=$NEO4J_AUTH     -p 80:7474     -p 7687:7687   --env AWS_DEFAULT_REGION=ap-southeast-2  rdkls/aws_infra_map
869f1634c1267e04ccb69f3cb3eed6c09779d4dcd0e1ade5c73a4e17106a40cf
mbp:~ nick - mocorp$ docker logs -f aws_mocorp_infra_map
Changed password for user 'neo4j'.
Active database: graph.db
Directories in use:
  home:         /var/lib/neo4j
  config:       /var/lib/neo4j/conf
  logs:         /var/lib/neo4j/logs
  plugins:      /var/lib/neo4j/plugins
  import:       /var/lib/neo4j/import
  data:         /var/lib/neo4j/data
  certificates: /var/lib/neo4j/certificates
  run:          /var/lib/neo4j/run
Starting Neo4j.
waiting for neo4j to start ...
waiting for neo4j to start ...
2018-06-25 08:05:41.799+0000 INFO  ======== Neo4j 3.3.2 ========
2018-06-25 08:05:41.854+0000 INFO  Starting...
waiting for neo4j to start ...
2018-06-25 08:05:43.448+0000 INFO  Bolt enabled on 0.0.0.0:7687.
waiting for neo4j to start ...
waiting for neo4j to start ...
waiting for neo4j to start ...
waiting for neo4j to start ...
waiting for neo4j to start ...
waiting for neo4j to start ...
waiting for neo4j to start ...
waiting for neo4j to start ...
waiting for neo4j to start ...
waiting for neo4j to start ...
2018-06-25 08:05:53.414+0000 INFO  Started.
waiting for neo4j to start ...
2018-06-25 08:05:54.591+0000 INFO  Remote interface available at http://localhost:7474/
waiting for neo4j to start ...
awless sync for region ap-south-1

 █████╗  ██╗    ██╗ ██╗     ██████  ██████╗ ██████╗
██╔══██╗ ██║    ██║ ██║     ██╔══╝  ██╔═══╝ ██╔═══╝
███████║ ██║ █╗ ██║ ██║     ████╗   ██████  ██████
██╔══██║ ██║███╗██║ ██║     ██╔═╝       ██╗     ██╗
██║  ██║ ╚███╔███╔╝ ██████╗ ██████╗ ██████║ ██████║
╚═╝  ╚═╝  ╚══╝╚══╝  ╚═════╝ ╚═════╝ ╚═════╝ ╚═════╝

Welcome! Resolving environment data...

Found existing AWS region 'ap-southeast-2'. Setting it as your default region.

All done. Enjoy!
You can review and configure awless with `awless config`

Now running: `awless sync`
[info]    running sync for region 'ap-south-1'
[info]    -> cloudformation: 0 stack
[info]    -> dns: 0 record, 1 zone
[info]    -> cdn: 0 distribution
[info]    -> lambda: 0 function
[info]    -> access: 1 mfadevice, 1 group, 36 roles, 11 policies, 5 accesskeys, 10 instanceprofiles, 4 users
[info]    -> infra: 0 classicloadbalancer, 0 launchconfiguration, 1 securitygroup, 0 containertask, 1 vpc, 2 availabilityzones, 0 image, 0 importimagetask, 0 snapshot, 0 networkinterface, 0 targetgroup, 0 database, 1 internetgateway, 0 natgateway, 1 routetable, 0 loadbalancer, 0 scalinggroup, 0 containercluster, 0 containerinstance, 0 certificate, 0 instance, 0 elasticip, 2 subnets, 0 dbsubnetgroup, 0 scalingpolicy, 0 container, 0 keypair, 0 volume, 0 listener, 0 repository
awless sync for region eu-west-1

load file /var/lib/neo4j/import/eu-west-1-lambda.corrected.nt
load file /var/lib/neo4j/import/eu-west-1-infra.corrected.nt
load file /var/lib/neo4j/import/eu-west-1-cloudformation.corrected.nt
load file /var/lib/neo4j/import/eu-west-1-messaging.corrected.nt
load file /var/lib/neo4j/import/eu-west-1-storage.corrected.nt
awless sync for region ap-northeast-2

load file /var/lib/neo4j/import/ap-northeast-2-lambda.corrected.nt
load file /var/lib/neo4j/import/ap-northeast-2-infra.corrected.nt
load file /var/lib/neo4j/import/ap-northeast-2-cloudformation.corrected.nt
load file /var/lib/neo4j/import/ap-northeast-2-messaging.corrected.nt
load file /var/lib/neo4j/import/ap-northeast-2-storage.corrected.nt
awless sync for region ap-northeast-1

load file /var/lib/neo4j/import/ap-northeast-1-lambda.corrected.nt
load file /var/lib/neo4j/import/ap-northeast-1-infra.corrected.nt
load file /var/lib/neo4j/import/ap-northeast-1-cloudformation.corrected.nt
load file /var/lib/neo4j/import/ap-northeast-1-messaging.corrected.nt2018-06-25 08:06:45.896+0000 INFO  Found 0 namespaces in the DB: {}
load file /var/lib/neo4j/import/us-west-2-lambda.corrected.nt
load file /var/lib/neo4j/import/us-west-2-infra.corrected.nt2018-06-25 08:07:45.269+0000 INFO  Found 0 namespaces in the DB: {}
2018-06-25 08:07:45.288+0000 INFO  Successfully committed 2 triples. Total number of triples imported is 2
2018-06-25 08:07:45.304+0000 INFO  Found 0 namespaces in the DB: {}
2018-06-25 08:07:45.390+0000 INFO  Successfully committed 774 triples. Total number of triples imported is 774
2018-06-25 08:07:45.402+0000 INFO  Found 0 namespaces in the DB: {}
2018-06-25 08:07:45.411+0000 INFO  Successfully committed 2 triples. Total number of triples imported is 2
2018-06-25 08:07:45.424+0000 INFO  Found 0 namespaces in the DB: {}
2018-06-25 08:07:45.446+0000 INFO  Successfully committed 15 triples. Total number of triples imported is 15
2018-06-25 08:07:45.461+0000 INFO  Found 0 namespaces in the DB: {}
2018-06-25 08:07:45.495+0000 INFO  Successfully committed 13 triples. Total number of triples imported is 13

load file /var/lib/neo4j/import/us-west-2-cloudformation.corrected.nt
load file /var/lib/neo4j/import/us-west-2-messaging.corrected.nt
load file /var/lib/neo4j/import/us-west-2-storage.corrected.nt
neo4j console
```


test

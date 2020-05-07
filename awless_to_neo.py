#!/usr/bin/env python
# Load your AWS environment into neo4j
#   - use awless to query aws, store resource descriptions in badwolf rdf stores
#   - clean thse files to be rdf-compliant
#   - load into neo4j with semantic importer
#   - update graph with node labels and properties for niceness
#
# awless uses standard aws env vars to do its thing; just set these as desired before running
#
# Examples:
#
# Do it all
# ./awless_to_neo.py
#
# Do one region, using existing badwolf dbs
# ./awless_to_neo.py --region=ap-southeast-2 --skip-sync
#
# References:
#
# awless
# https://github.com/wallix/awless

# RDF loader by jbarrasa
# https://jbarrasa.com/2016/06/07/importing-rdf-data-into-neo4j/
# https://github.com/jbarrasa/neosemantics

from neo4j.exceptions import ServiceUnavailable
from neo4j.v1 import GraphDatabase
from pprint import pprint
import argparse
import boto3
import json
import os
import re
import subprocess
import neobolt

DEBUG = True
AWLESS_DATABASE_PATH = '/root/.awless/aws/rdf/default/%s/'
CORRECTED_SUFFIX = '.corrected.nt'
THE_NEO4J_BASEDIR='/var/lib/neo4j'

THE_NEO4J_BASEDIR_DEBUG = '/Users/nick.doyle/ws/3rdparty/neo4j/aws_infra_map'
AWLESS_DATABASE_PATH_DEBUG = '/Users/nick.doyle/.awless/aws/rdf/default/%s/'

def get_neo4j_auth():
    (user, password) = os.environ.get('NEO4J_AUTH').split('/')
    return (user, password)

def correct_file(infile, region, debug):
    # Output file will be prefix of the input file + '.corrected.nt'
    # In the neo4j import dir
    # (neo4j security requirement in order to be able to import)
    (prefix, suffix) = os.path.splitext(os.path.split(infile)[1])
    outfile = region + '-' + prefix + CORRECTED_SUFFIX
    if debug:
        neo4j_basedir = THE_NEO4J_BASEDIR_DEBUG
    else:
        neo4j_basedir = THE_NEO4J_BASEDIR
    outfile = os.path.join(neo4j_basedir, 'import', outfile)

    with open(outfile, 'w') as of:
        with open(infile, 'r') as f:
            for line in f:
                line = line.strip()
                (sub, pred, obj) = re.match('([^\s]+) ([^\s]+) (.*) \.', line).groups()

                # SUB
                # Prepend resource: if needed
                if re.match('<[^:]*>', sub):
                    sub = re.sub('<(.*)>', '<resource:\\1>', sub)

                # OBJ
                # Prepend resource: if needed
                if re.match('<[^:]*>', obj):
                    obj = re.sub('<(.*)>', '<resource:\\1>', obj)

                # For s3 grantees, for some reason they have this format which causes it to be discarded hence not linked to the grant ...
                obj = re.sub('_:(.*)', '<resource:\\1>', obj)

                # Trim ^^ and anything following (happens when type is specified - we don't care they're all strings
                obj = re.sub("(.+)\^\^.*", '\\1', obj)

                # Replace <cloud-owl:*> with *
                obj = re.sub("<cloud-owl:([^>]+)>", '"\\1"', obj)

                # Replace <net-owl:*> with *
                obj = re.sub("<net-owl:([^>]+)>", '"\\1"', obj)

                # Move id to cloud_id; in cases where these are ARNs or UUIDs
                # They won't get imported
                # Hence we leave neo4j to set the node ID
                # And move thse to their own prop "cloud_id" for later use/cleaning
                # Replace <cloud:id> with <cloud:cloud_id>
                pred = re.sub("<cloud:id>", "<cloud:cloud_id>", pred)

                of.write('%s %s %s .\n' % (sub, pred, obj))
    return outfile


def init_graph():
    d = GraphDatabase.driver('bolt://127.0.0.1:7687', auth=get_neo4j_auth(), encrypted=False)
    with d.session() as session:
        # Create required indexes
        cypher = 'CREATE CONSTRAINT n10s_unique_uri ON (r:Resource) ASSERT r.uri IS UNIQUE'
        try:
            session.run(cypher)
        except neobolt.exceptions.ClientError:
            # Index already exists
            pass

        # Init graph config for semantics plugin
        cypher = 'CALL n10s.graphconfig.init()'
        try:
            session.run(cypher)
        except neobolt.exceptions.ClientError:
            # Index already exists
            pass


def load_to_neo4j(filenames):
    # Load the corrected rdj files from neo4j/import, into the db
    d = GraphDatabase.driver('bolt://127.0.0.1:7687', auth=get_neo4j_auth(), encrypted=False)
    with d.session() as session:
        for fn in filenames:
            # use jbarrasa's plugin to load the now-correct rdf into neo4j
            # see https://github.com/jbarrasa/neosemantics
            print 'load file %s' % fn
            cypher = "call n10s.rdf.import.fetch('file:///%s', 'N-Triples', {shortenUrls: false})" % fn
            with session.begin_transaction() as tx:
                res = tx.run(cypher)
                res.consume()
                for r in res:
                    continue
            print('... loaded')


def fix_db():
    print('Fixing the Graph DB Labels, Props and Relationships with a bunch of dody inferences .....')

    # Fix up the db for niceess - add node labels, set names
    d = GraphDatabase.driver('bolt://127.0.0.1:7687', auth=get_neo4j_auth(), encrypted=False)
    pprint(d)
    with d.session() as session:
        # Remove generic 'Resource:' label
        cypher = """
            match (n)
            where n:Resource
            CALL apoc.create.removeLabels(n, ['Resource'])
            YIELD node
            RETURN node
        """
        session.run(cypher)

        # Strip redundant resource: on names & uris
        # (we hacked this on before so RDF import didn't fail)
        cypher = """
            match (n)
            CALL apoc.create.setProperty(n, 'name', replace(n.name, 'resource:', ''))
            YIELD node
            RETURN node
        """
        session.run(cypher)
        cypher = """
            match (n)
            CALL apoc.create.setProperty(n, 'uri', replace(n.uri, 'resource:', ''))
            YIELD node
            RETURN node
        """
        session.run(cypher)

        # Merge on ns0 & ns1 cloud_id
        # (don't do all in one query lest you break neo4j)
        cypher = """
            MATCH   (n),
                    (p)
            WHERE   exists(n.ns0__cloud_id)
                    and
                    n.ns0__cloud_id = p.ns0__cloud_id
                    and
                    id(n) < id(p)
            WITH    [n,p] as nodes
            CALL    apoc.refactor.mergeNodes(nodes)
            YIELD   node
            RETURN  node
        """
        session.run(cypher)
        cypher = """
            MATCH   (n),
                    (p)
            WHERE   exists(n.ns1__cloud_id)
                    and
                    n.ns1__cloud_id = p.ns1__cloud_id
                    and
                    id(n) < id(p)
            WITH    [n,p] as nodes
            CALL    apoc.refactor.mergeNodes(nodes)
            YIELD   node
            RETURN  node
        """
        session.run(cypher)

        # AMIs and AMI Locations
        # Need to do this before setting Label based on ns0__type
        # Since AMIs have this field set to "machine"
        session.run("match (n) where n.uri =~ '^ami-.*' set n:Ami")
        session.run("match (n)<-[:ns0__location]-(:Ami) where not labels(n) set n:AmiLocation")

        # Set label based on ns0__type preferably
        # then ns1 (the more-specific)
        cypher = """
            match (n)
            where not labels(n)
            CALL apoc.create.addLabels(n, [n.ns0__type])
            YIELD node
            RETURN node
        """
        session.run(cypher)
        cypher = """
            match (n)
            where not labels(n)
            CALL apoc.create.addLabels(n, [n.ns1__type])
            YIELD node
            RETURN node
        """
        session.run(cypher)

        # Set Name on ns0__name preferably
        # then ns1 (the more-specific)
        cypher = """
            match (n)
            where not labels(n)
            CALL apoc.create.setProperty(n, 'name', n.ns0__name)
            YIELD node
            RETURN node
        """
        session.run(cypher)
        cypher = """
            match (n)
            where not labels(n)
            CALL apoc.create.setProperty(n, 'name', n.ns1__name)
            YIELD node
            RETURN node
        """
        session.run(cypher)

        session.run("match (n) where n.name =~ '^arn:aws:iam::.*:role.*' set n:Role")
        session.run("match (n) where n.name =~ '^arn:aws:sns:.*' set n:SNSTopic")
        session.run("match ()-[:`cloud:grantee`]->(n) set n:Grantee")
        session.run("match (n {`cloud:granteeType`: 'CanonicalUser'}) set n:Grantee")
        session.run("match ()-[:`cloud:securityGroups`]->(n) set n:Securitygroup")
        session.run("match (n) where n.uri =~ '^subnet.*' set n:Subnet")
        session.run("match (n) where n.uri =~ '.*FirewallRule.*' set n:FirewallRule")
        session.run("match (n) where n.uri =~ '.*Route.*' set n:Route")
        session.run("match (n) where n.uri =~ '^vpc-.*' set n:Vpc")
        session.run("match (n) where n.uri =~ '^vol-.*' set n:Volume")
        session.run("match (n)<-[:ns0__role]-() where not labels(n) set n:Role")
        session.run("match (n)<-[:ns0__location]-(:Image) where not labels(n) set n:ImageLocation")
        session.run("match (n)<-[:ns1__zone]-() where not labels(n) set n:Route53HostedZone")
        session.run("match (n)<-[:ns1__associations]-() set n:RoutetableAssociation")

        # Relate route table associations
        session.run("""
            match   (a:RoutetableAssociation),
                    (s:Subnet)
            where   a.ns1__value = s.ns1__id
            merge   (a)-[:ns1__associationTo]->(s)
        """)

        # ECS
        session.run("match (n)<-[:ns1__containersImages]-() where (not labels(n) or n:KeyValue) set n:Containerimage")
        session.run("match (n:Containertask) set n.arn = n.name")
        session.run("match (n:Container) where exists(n.ns0__name) set n.name = n.ns0__name")
        session.run("match (n:Containertask) where exists(n.arn) set n.name = apoc.text.replace(n.arn, '^.*?/', '')")
        session.run("match (n:Containertask) where exists(n.ns1__arn) set n.name = apoc.text.replace(n.ns1__arn, '^.*?/', '')")
        session.run("match (n:Containertask) where exists(n.ns0__arn) set n.name = apoc.text.replace(n.ns0__arn, '^.*?/', '')")
        session.run("match (n:Containercluster) where exists(n.name) set n.arn = n.name")
        session.run("match (n:Containercluster) where exists(n.ns0__arn) set n.arn = n.ns0__arn")
        session.run("match (n:Containercluster) set n.name = apoc.text.replace(n.arn, '^.*?/', '')")

        # SNS & SQS
        session.run("match (n:Topic) set n:SnsTopic")
        session.run("match (n)<-[:ns0__topic]-() set n:SnsTopic")
        session.run("match (n) where n:Topic CALL apoc.create.removeLabels(n, ['Topic']) YIELD node return node")
        session.run("match (n:SnsTopic) set n.name = apoc.text.replace(n.uri, '^.*:', '')")
        session.run("match (n:SnsTopic) set n.name = apoc.text.replace(n.name, '^.*:', '')")
        session.run("match (n:Subscription) set n.name = apoc.text.replace(n.name, '^.*:', '')")
        # Link up SNS Subscriptions to SQS Queues
        session.run("match (s:Subscription), (q) where s.uri = q.ns0__arn merge (s)-[:subscription]->(q)")
        session.run("match (n:Queue) set n.name = apoc.text.replace(n.name, '^.*:', '')")

        # Lambdas (:Function)
        session.run("match (n:Function) set n:Lambda")
        session.run("match (n) where n:Function CALL apoc.create.removeLabels(n, ['Function']) YIELD node return node")
        session.run("match (n:Lambda) set n.name=n.ns0__name")


        # LBs & Target Groups
        session.run("match (n)<-[:ns3__applyOn]-(:Targetgroup) where not labels(n) set n:TargetgroupTarget")
        session.run("""
            match   (n:TargetgroupTarget),
                    (p:Networkinterface)
            where   n.uri = p.ns2__privateIP
            merge   (n)-[:trafficTo]->(p)
        """)
        session.run("""
            match   (n:Listener),
                    (p:Targetgroup)
            where   n.ns1__targetGroups = p.ns1__arn
            merge   (n)-[:forwardsTo]->(p)
        """)
        session.run("match (n:Targetgroup) set n.name=n.ns1__name")
        session.run("match (n:Loadbalancer) set n.name=n.ns1__name")
        session.run("match (n:Listener) set n.name=n.ns2__protocol + ':' + n.ns2__port")

        # Names on SGs
        session.run("match (n:FirewallRule) set n.name=n.ns2__cidr")
        session.run("match (n:FirewallRule) where not exists(n.name) set n.name=n.ns1__source")

        session.run("""
            match  (n)
            where   n.uri =~ '^arn:aws:iam:.*:role/.*'
            set     n:Role,
                    n.name = apoc.text.replace(n.uri, '^.*?/', '')
        """)

        # Label public and Private Subnets
        session.run("""
            match   (s:Subnet)<-[:ns3__applyOn]-(rt:Routetable)-[:ns2__routes]->(r:Route)
            where   r.ns2__cidr='0.0.0.0/0'
                    and
                    r.ns2__routeTargets =~ '.*igw-.*'
            set     s:SubnetPublic
        """)
        session.run("""
            match   (s:Subnet)<-[:ns3__applyOn]-(rt:Routetable)-[:ns2__routes]->(r:Route)
            where   r.ns2__cidr='0.0.0.0/0'
                    and
                    r.ns2__routeTargets =~ '.*nat-.*'
            set     s:SubnetPrivate
        """)

        session.run("match (n:Queue) set n.name = apoc.text.replace(n.ns0__arn, '^.*?/', '')")

        # Not super sure on "Grantee"
        session.run("match (n) where n.ns0__granteeType = 'CanonicalUser' and not labels(n) set n:Grantee")
        session.run("match (n)<-[:ns0__grantee]-() where not labels(n) set n:Grantee")
        session.run("match (n)<-[:ns1__grantee]-() where not labels(n) set n:Grantee")
        session.run("match (n:Grantee) set n.name = n.ns0__name")
        session.run("match (n:Grantee) where n.name is null and n.ns1__name is not null set n.name = n.ns1__name")
        session.run("match (n:Grant) where n.ns0__permission is not null set n.name = n.ns0__permission")
        session.run("match (n:Grant) where n.ns1__permission is not null set n.name = n.ns1__permission")

        # Set node labels - based on node props
        res = session.run('match (n) where n.`rdf:type` is not null return n')
        set_of_labels_to_apply = set()
        for record in res:
            set_of_labels_to_apply.add(record['n']['rdf:type'])
        for label in set_of_labels_to_apply:
            cypher = 'match (n) where n.`rdf:type`="%s" set n:%s' % (label, label)
            session.run(cypher)

        # Set node labels - based on relationship props
        cypher = 'match ()-[r:`rdf:type`]->(t) return t'
        res = session.run(cypher)
        set_of_labels_to_apply = set()
        for record in res:
            set_of_labels_to_apply.add(record['t']['uri'])

        for rdf_type in set_of_labels_to_apply:
            # Do the updates
            # node label just remove anything before colon
            label = re.sub('.*:([^:]*)', '\\1', rdf_type)
            cypher = 'match (n)-[:`rdf:type`]->(t {uri: "%s"}) set n:%s' % (rdf_type, label)
            session.run(cypher)

        # Set node names
        # from various properties, in descending order of preference
        propnames = [
            'cloud:name',
            'cloud:keyName',
            'cloud:id',
            'cloud:cloud_id',
            'cloud:permission',
            'uri',
        ]
        for propname in propnames:
            session.run('match (n) where  n.`%s` is not null and n.name is null set n.name = n.`%s`' % (propname, propname))

    print(' AAAAAAAAAARE YOU READY TO RUUUUUUUUUUMBLE ')
    # By this point we hope the user is ready to rumble

def get_all_regions():
    ec2 = boto3.client('ec2')
    res = ec2.describe_regions()
    regions = map(lambda x: x['RegionName'], res['Regions'])
    return regions

if '__main__' == __name__:
    parser = argparse.ArgumentParser(description='Grab representation of your AWS environment into neo4j')
    parser.add_argument('--region', help='limit to one aws region')
    parser.add_argument('--infile', '-i', help='one awless n-triple db file to run with')
    parser.add_argument('--skip-sync', '-s', action='store_true', help='skip awless sync; operate on local db files only')
    parser.add_argument('--only-fix-db', action='store_true', help='only fix db')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--debug', action='store_true')

    args = parser.parse_args()

    init_graph()

    if args.only_fix_db:
        print('i only fix the db!')
        fix_db()
        import sys;sys.exit(0) # don't tell arjen

    if not args.infile:
        if args.region:
            regions = [args.region]
        elif os.environ.get('AWS_TO_NEO4J_LIMIT_REGION'):
            regions = [os.environ.get('AWS_TO_NEO4J_LIMIT_REGION')]
        else:
            regions = get_all_regions()

        for region in regions:
            if not args.skip_sync:
                print 'awless sync for region %s' % region
                print subprocess.check_output(['/usr/local/bin/awless', 'sync', '--aws-region=%s' % region])

            # Correct all files
            corrected_filepaths = []
            if args.debug:
                awless_database_path = AWLESS_DATABASE_PATH_DEBUG
            else:
                awless_database_path = AWLESS_DATABASE_PATH
            try:
                fns = os.listdir(awless_database_path % region)
            except OSError:
                print "can't load files from %s, skipping ..." % awless_database_path % region
                continue

            for fn in fns:
                if not fn.endswith(CORRECTED_SUFFIX):
                    fullpath = os.path.join(awless_database_path % region, fn)
                    corrected_filepaths.append(correct_file(fullpath, region, args.debug))
            if args.verbose:
                print 'corrected files:'
                from pprint import prpint;pprint(corrected_filepaths)
            load_to_neo4j(corrected_filepaths)

        fix_db()

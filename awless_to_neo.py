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
import argparse
import boto3
import json
import os
import re
import subprocess

AWLESS_DATABASE_PATH = '/root/.awless/aws/rdf/default/%s/'
CORRECTED_SUFFIX = '.corrected.nt'
THE_NEO4J_BASEDIR='/var/lib/neo4j'

def get_neo4j_auth():
    (user, password) = os.environ.get('NEO4J_AUTH').split('/')
    return (user, password)

def correct_file(infile, region):
    # Output file will be prefix of the input file + '.corrected.nt'
    # In the neo4j import dir
    # (neo4j security requirement in order to be able to import)
    (prefix, suffix) = os.path.splitext(os.path.split(infile)[1])
    outfile = region + '-' + prefix + CORRECTED_SUFFIX
    outfile = os.path.join(THE_NEO4J_BASEDIR, 'import', outfile)

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

                # Trim ^^ and anything following (happens when type is specified - we don't care they're all strings
                obj = re.sub("(.+)\^\^.*", '\\1', obj)

                # Replace <cloud-owl:*> with *
                obj = re.sub("<cloud-owl:([^>]+)>", '"\\1"', obj)

                of.write('%s %s %s .\n' % (sub, pred, obj))
    return outfile


def load_to_neo4j(filenames):
    # Load the corrected rdj files from neo4j/import, into the db
    d = GraphDatabase.driver('bolt://localhost:7687', auth=get_neo4j_auth())
    with d.session() as session:
        # Create required indexes
        cypher = 'create index on :Resource(uri)'
        session.run(cypher)

        for fn in filenames:
            # use jbarrasa's plugin to load the now-correct rdf into neo4j
            # see https://github.com/jbarrasa/neosemantics
            print 'load file %s' % fn
            cypher = "call semantics.importRDF('file:///%s', 'N-Triples', {shortenUrls: false})" % fn
            res = session.run(cypher)

def fix_db():
    # Fix up the db for niceess - add node labels, set names
    d = GraphDatabase.driver('bolt://localhost:7687', auth=get_neo4j_auth())

    with d.session() as session:

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
            'cloud:permission',
            'uri',
        ]
        for propname in propnames:
            session.run('match (n) where  n.`%s` is not null and n.name is null set n.name = n.`%s`' % (propname, propname))

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
    parser.add_argument('--fix-db', action='store_true', help='only fix db')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    if args.fix_db:
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
            try:
                fns = os.listdir(AWLESS_DATABASE_PATH % region)
            except OSError:
                print "can't load files from %s, skipping ..." % AWLESS_DATABASE_PATH % region
                continue

            for fn in fns:
                if not fn.endswith(CORRECTED_SUFFIX):
                    fullpath = os.path.join(AWLESS_DATABASE_PATH % region, fn)
                    corrected_filepaths.append(correct_file(fullpath, region))
            if args.verbose:
                print 'corrected files:'
                from pprint import prpint;pprint(corrected_filepaths)
            load_to_neo4j(corrected_filepaths)

        fix_db()

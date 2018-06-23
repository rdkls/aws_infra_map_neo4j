#!/usr/bin/env python

# https://jbarrasa.com/2016/06/07/importing-rdf-data-into-neo4j/
# https://github.com/jbarrasa/neosemantics

import argparse
import re
import os
from neo4j.v1 import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
import subprocess

AWLESS_DATABASE_PATH = '/root/.awless/aws/rdf/default/%s/'
CORRECTED_SUFFIX = '.corrected.nt'
NEO4J_PASSWORD_DEFAULT = 'awsmap'

def get_neo4j_password():
    return os.environ.get('NEO4J_PASSWORD', NEO4J_PASSWORD_DEFAULT)

def set_neo4j_password():
    try:
        d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'neo4j'))
        print 'don'
    except ServiceUnavailable:
        # must have already set ...
        return

    with d.session() as session:
        print 't2'
        session.run("CALL dbms.changePassword('%s')" % get_neo4j_password())
        print 'd2'
    print 'set neo4j password to "%s"' % get_neo4j_password()

def correct_file(infile):
    outfile = infile + CORRECTED_SUFFIX
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


def load_to_neo4j(files):
    set_neo4j_password()
    d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', get_neo4j_password()))
    with d.session() as session:
        for fn in files:
            res = session.run("call semantics.importRDF('file:///%s', 'N-Triples', {shortenUrls: false})" % fn)
            print res


if '__main__' == __name__:
    parser = argparse.ArgumentParser(description='Convert awless-outputted .nt files to triplestores conforming to w3c rdf spec, ntriple')
    parser.add_argument('--all', '-a', action='store_true')
    parser.add_argument('--infile', '-i')
    parser.add_argument('--outfile', '-o')
    parser.add_argument('--awless', action='store_true')
    parser.add_argument('--fixdb', action='store_true')
    args = parser.parse_args()

    if args.awless:
        # TODO multi region
        region = os.environ.get('AWS_DEFAULT_REGION', os.environ.get('REGION', None))
        print subprocess.check_output(['/usr/local/bin/awless', 'sync', '--aws-region=%s' % region])

    if args.all:
        # TODO multi region
        region = os.environ.get('AWS_DEFAULT_REGION', os.environ.get('REGION', None))
        print subprocess.check_output(['/usr/local/bin/awless', 'sync', '--aws-region=%s' % region])

        # Correct all files
        region = os.environ.get('AWS_DEFAULT_REGION', os.environ.get('REGION', None))
        corrected_filepaths = []
        for fn in os.listdir(AWLESS_DATABASE_PATH % region):
            if not fn.endswith(CORRECTED_SUFFIX):
                fullpath = os.path.join(AWLESS_DATABASE_PATH % region, fn)
                corrected_filepaths.append(correct_file(fullpath))
        print(corrected_filepaths)
        load_to_neo4j(corrected_filepaths)

    if args.infile:
        correct_file(args.infile)

    if args.fixdb:
        d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'p'))
        with d.session() as session:
            res = session.run('match (n) where n.`rdf:type` is not null return n')
            s = set()
            for record in res:
                s.add(record['n']['rdf:type'])
            for t in s:
                c = 'match (n) where n.`rdf:type`="%s" set n:%s' % (t, t)
                session.run(c)
            session.run('match (n) where  n.`cloud:keyName` is not null and n.name is null set n.name = n.`cloud:keyName`')
            session.run('match (n) where  n.`cloud:name` is not null and n.name is null set n.name = n.`cloud:name`')
            session.run('match (n) where  n.`cloud:id` is not null and n.name is null set n.name = n.`cloud:id`')


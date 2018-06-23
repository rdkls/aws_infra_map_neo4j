#!/usr/bin/env python

# https://jbarrasa.com/2016/06/07/importing-rdf-data-into-neo4j/
# https://github.com/jbarrasa/neosemantics

import argparse
import re
from neo4j.v1 import GraphDatabase

if '__main__' == __name__:
    parser = argparse.ArgumentParser(description='Convert awless-outputted .nt files to triplestores conforming to w3c rdf spec, ntriple')
    parser.add_argument('--infile', '-i', default='lambda.nt')
    parser.add_argument('--outfile', '-o')
    parser.add_argument('--fixdb', action='store_true')
    args = parser.parse_args()

    if not args.outfile:
        args.outfile = args.infile + '.corrected.nt'

    if not args.fixdb:
        with open(args.infile, 'r') as f:
            for line in f:
                line = line.strip()
                #print(line.split(' '))
                #print line
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

                print('%s %s %s .' % (sub, pred, obj))
            
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

#!/bin/bash
neo4j start
while sleep 1 ; do
    if [[ `tail -n2 /var/lib/neo4j/logs/neo4j.log | grep 'Remote interface available'` ]] ; then
        /bin/bash
    fi
    echo "waiting for neo4j to start ..."
done

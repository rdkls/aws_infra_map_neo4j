#!/bin/bash
neo4j start
no_success=true
while $no_success ; do
    sleep 1
    echo "waiting for neo4j to start ..."
    if [[ `tail -n2 /var/lib/neo4j/logs/neo4j.log | grep 'Remote interface available'` ]] ; then
        no_success=false
        /bin/bash
    fi
done

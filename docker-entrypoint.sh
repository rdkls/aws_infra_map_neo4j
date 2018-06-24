#!/bin/bash
set -m

if [[ -z "$AWS_DEFAULT_REGION$AWS_TO_NEO4J_LIMIT_REGION" ]] ; then
    echo 'AWS_DEFAULT_REGION or AWS_TO_NEO4J_LIMIT_REGION must be set'
    exit 1
fi
# Be kind and set default region if only limit was specified
if [[ -z $AWS_DEFAULT_REGION ]] ; then
    export AWS_DEFAULT_REGION=$AWS_TO_NEO4J_LIMIT_REGION
fi
if [[ -z "$NEO4J_AUTH" ]] ; then
    echo 'NEO4J_AUTH must be set to user/pass'
    exit 1
fi
if [[ -z "$AWS_SECRET_ACCESS_KEY" ]] ; then
    echo 'AWS_SECRET_ACCESS_KEY must be set'
    exit 1
fi
if [[ -z "$AWS_ACCESS_KEY_ID" ]] ; then
    echo 'AWS_ACCESS_KEY_ID must be set'
    exit 1
fi

THE_NEO4J_BASEDIR=/var/lib/neo4j

# Custom settings for dockerized neo4j
: ${NEO4J_dbms_tx__log_rotation_retention__policy:=100M size}
: ${NEO4J_dbms_memory_pagecache_size:=512M}
: ${NEO4J_wrapper_java_additional:=-Dneo4j.ext.udc.source=docker}
: ${NEO4J_dbms_memory_heap_initial__size:=512M}
: ${NEO4J_dbms_memory_heap_max__size:=512M}
: ${NEO4J_dbms_connectors_default__listen__address:=0.0.0.0}
: ${NEO4J_dbms_connector_http_listen__address:=0.0.0.0:7474}
: ${NEO4J_dbms_connector_https_listen__address:=0.0.0.0:7473}
: ${NEO4J_dbms_connector_bolt_listen__address:=0.0.0.0:7687}

# set the neo4j initial password only if you run the database server
if [ "${NEO4J_AUTH:-}" == "none" ]; then
    NEO4J_dbms_security_auth__enabled=false
elif [[ "${NEO4J_AUTH:-}" == neo4j/* ]]; then
    password="${NEO4J_AUTH#neo4j/}"
    if [ "${password}" == "neo4j" ]; then
        echo "Invalid value for password. It cannot be 'neo4j', which is the default."
        exit 1
    fi
    # Will exit with error if users already exist (and print a message explaining that)
    $THE_NEO4J_BASEDIR/bin/neo4j-admin set-initial-password "${password}" || true
elif [ -n "${NEO4J_AUTH:-}" ]; then
    echo "Invalid value for NEO4J_AUTH: '${NEO4J_AUTH}'"
    exit 1
fi

# list env variables with prefix NEO4J_ and create settings from them
#unset NEO4J_AUTH
unset NEO4J_SHA256 NEO4J_TARBALL
for i in $( set | grep ^NEO4J_ | awk -F'=' '{print $1}' | sort -rn ); do
    setting=$(echo ${i} | sed 's|^NEO4J_||' | sed 's|_|.|g' | sed 's|\.\.|_|g')
    value=$(echo ${!i})
    if [[ -n ${value} ]]; then
        if grep -q -F "${setting}=" $THE_NEO4J_BASEDIR/conf/neo4j.conf; then
            # Remove any lines containing the setting already
            sed --in-place "/${setting}=.*/d" $THE_NEO4J_BASEDIR/conf/neo4j.conf
        fi
        # Then always append setting to file
        echo "${setting}=${value}" >> $THE_NEO4J_BASEDIR/conf/neo4j.conf
    fi
done

# Start neo4j with console in background
# so we can load aws data, then later fg it
neo4j console&

# Wait for neo4j to come up
neo4j_not_up=true
while $neo4j_not_up ; do
    sleep 1
    echo "waiting for neo4j to start ..."
    if [[ 0 -eq `nc -z localhost 7474; echo $?` ]] ; then 
        neo4j_not_up=false
    fi
done

# Load aws data
/usr/local/bin/awless_to_neo.py

# fg neo4j console
fg 1

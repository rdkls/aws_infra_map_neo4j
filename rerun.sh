#!/usr/bin/env bash
NEO4J_AUTH='neo4j/paper'

if [ -z "$AWS_SECRET_ACCESS_KEY" ] ; then
	export AWS_SECRET_ACCESS_KEY=`grep aws_secret_access_key ~/.aws/credentials | head -n1 | cut -d'=' -f 2 | sed 's/ //g'`
	export AWS_ACCESS_KEY_ID=`grep aws_access_key_id ~/.aws/credentials | head -n1 | cut -d'=' -f 2 | sed 's/ //g'`
	export AWS_SESSION_TOKEN=`grep aws_session_token ~/.aws/credentials | head -n1 | cut -d'=' -f 2 | sed 's/ //g'`
	export AWS_SECURITY_TOKEN=`grep aws_security_token ~/.aws/credentials | head -n1 | cut -d'=' -f 2 | sed 's/ //g'`
	export AWS_REGION=`grep region ~/.aws/config | head -n1 | cut -d'=' -f 2 | sed 's/ //g'`
fi
export AWS_TO_NEO4J_LIMIT_REGION=$AWS_REGION
export NEO4J_AUTH=neo4j/paper

./awless_to_neo.py --only-fix-db

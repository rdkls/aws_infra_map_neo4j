#!/usr/bin/env bash
NEO4J_AUTH='neo4j/paper'

if [ -z "$AWS_SECRET_ACCESS_KEY" ] ; then
	# Get from files
	AWS_SECRET_ACCESS_KEY=`grep aws_secret_access_key ~/.aws/credentials | head -n1 | cut -d'=' -f 2 | sed 's/ //g'`
	AWS_ACCESS_KEY_ID=`grep aws_access_key_id ~/.aws/credentials | head -n1 | cut -d'=' -f 2 | sed 's/ //g'`
	AWS_SESSION_TOKEN=`grep aws_session_token ~/.aws/credentials | head -n1 | cut -d'=' -f 2 | sed 's/ //g'`
	AWS_SECURITY_TOKEN=`grep aws_security_token ~/.aws/credentials | head -n1 | cut -d'=' -f 2 | sed 's/ //g'`
	AWS_REGION=`grep region ~/.aws/config | head -n1 | cut -d'=' -f 2 | sed 's/ //g'`
fi
docker rm -f neo4j_awless 2>/dev/null
docker run -ti \
    --name neo4j_awless \
    --env AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    --env AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    --env AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
    --env AWS_TO_NEO4J_LIMIT_REGION=ap-southeast-2  \
    --env NEO4J_AUTH=$NEO4J_AUTH \
    -p 7474:7474 \
    -p 7687:7687 \
    rdkls/aws_infra_map_neo4j

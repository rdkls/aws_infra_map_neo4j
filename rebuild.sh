NEO4J_AUTH='neo4j/paper'

docker rm -f neo4j_awless 2>/dev/null
docker build --tag aws_map:3.3.2 .

docker run -ti \
    --name neo4j_awless \
    --env AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    --env AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    --env AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
    --env AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION  \
    --env AWS_TO_NEO4J_LIMIT_REGION=ap-southeast-2  \
    --env NEO4J_AUTH=$NEO4J_AUTH \
    -p 80:7474 \
    -p 7687:7687 \
    aws_map:3.3.2

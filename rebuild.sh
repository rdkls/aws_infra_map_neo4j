docker rm -f neo4j_awless 2>/dev/null
docker build --tag aws_map:3.3.2 .
docker run -ti aws_map:3.3.2 bash

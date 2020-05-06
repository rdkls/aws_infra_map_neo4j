FROM neo4j:4.0.0
EXPOSE 7474
EXPOSE 7687

# APOC + Neosemantics
RUN echo "dbms.security.procedures.unrestricted=apoc.trigger.*,apoc.meta.*" >> /var/lib/neo4j/conf/neo4j.conf
WORKDIR /var/lib/neo4j/plugins
RUN wget --quiet https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/download/4.0.0.10/apoc-4.0.0.10-all.jar
RUN wget --quiet https://github.com/neo4j-labs/neosemantics/releases/download/4.0.0.0/neosemantics-4.0.0.0.jar

# Install awless
WORKDIR /usr/local/bin
RUN wget --quiet https://github.com/wallix/awless/releases/download/v0.1.11/awless-linux-amd64.tar.gz
RUN tar -xzvf awless-linux-amd64.tar.gz

# Install awless_to_neo
RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get -yq install python python-pip netcat
RUN pip -q install --upgrade pip
COPY awless_to_neo.py /usr/local/bin
COPY requirements.txt /tmp
RUN pip -q install -r /tmp/requirements.txt

COPY docker-entrypoint.sh /
ENTRYPOINT []
CMD /docker-entrypoint.sh

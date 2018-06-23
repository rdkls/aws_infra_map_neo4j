FROM neo4j:3.3.2
ADD https://github.com/jbarrasa/neosemantics/releases/download/3.3.0.2/neosemantics-3.3.0.2.jar /var/lib/neo4j/plugins

ADD https://github.com/wallix/awless/releases/download/v0.1.11/awless-linux-amd64.tar.gz /usr/local/bin
WORKDIR /usr/local/bin
RUN tar -xzvf awless-linux-amd64.tar.gz

RUN mkdir -p /opt/awless_to_neo
WORKDIR /opt/awless_to_neo
ADD awless_to_neo.py .
ADD requirements.txt .
RUN pip install -r requirements.txt

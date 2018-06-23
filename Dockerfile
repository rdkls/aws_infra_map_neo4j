FROM neo4j:3.3.2
WORKDIR /var/lib/neo4j/plugins
RUN wget https://github.com/jbarrasa/neosemantics/releases/download/3.3.0.2/neosemantics-3.3.0.2.jar

WORKDIR /usr/local/bin
RUN wget https://github.com/wallix/awless/releases/download/v0.1.11/awless-linux-amd64.tar.gz
RUN tar -xzvf awless-linux-amd64.tar.gz

RUN mkdir -p /opt/awless_to_neo
WORKDIR /opt/awless_to_neo
ADD awless_to_neo.py .
ADD requirements.txt .
RUN apk update
RUN apk add py2-pip
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

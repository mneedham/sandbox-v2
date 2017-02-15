FROM neo4j:3.1-enterprise

RUN apk add --no-cache --quiet \
  python \
  py-pip \
  zip

RUN pip install --upgrade pip
RUN pip install boto3

RUN ln -sf /dev/stdout /var/lib/neo4j/logs/query.log \
        && ln -sf /dev/stderr /var/lib/neo4j/logs/debug.log

RUN ln -sf /dev/stderr /var/lib/neo4j/logs/security.log

COPY ./backup-server.py /

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["neo4j"]

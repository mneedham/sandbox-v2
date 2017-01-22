FROM neo4j:3.1-enterprise

RUN apk add --no-cache --quiet \
  python \
  py-pip \
  zip

RUN pip install boto3

COPY ./backup-server.py /

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["neo4j"]

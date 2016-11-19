#!/usr/bin/python

from neo4j.v1 import GraphDatabase, basic_auth
from retrying import retry
import os
import boto3

NEO4J_HOST = os.environ["NEO4J_HOST"]
NEO4J_AUTH = os.environ["NEO4J_AUTH"]
USECASE = os.environ["USECASE"]
CONNECT_NEO4J_RETRIES = 10
CONNECT_NEO4J_WAIT_SECS = 3

def get_db_creds():
  global NEO4J_AUTH
  return {'user': (NEO4J_AUTH.split("/"))[0],
          'password': (NEO4J_AUTH.split("/"))[1]}

@retry(stop_max_attempt_number=CONNECT_NEO4J_RETRIES, wait_fixed=(CONNECT_NEO4J_WAIT_SECS * 1000))
def get_db_session():
  global NEO4J_HOST
  creds = get_db_creds()
  driver = GraphDatabase.driver("bolt://%s" % (NEO4J_HOST), auth=basic_auth(creds['user'], creds['password']), encrypted=False)
  session = driver.session()
  return session

def import_data():
  global USECASE
  session = get_db_session()
  s3 = boto3.client('s3')
  response = s3.get_object(Bucket='neo4j-sandbox-import-scripts',Key='%s.cyp' % (USECASE))
  queries = response['Body'].read()
  
  query = queries.split(";\n")
  for query in queries:
    print("###### Executing query:\n%s" % (query))
    results = session.run(query, parameters={})
    for record in results:
      print(record)
  
import_data()

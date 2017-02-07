#!/usr/bin/python

from neo4j.v1 import GraphDatabase, basic_auth
from retrying import retry
import os
import boto3
import botocore

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
  s3 = boto3.client('s3')
  try:
    response = s3.get_object(Bucket='neo4j-sandbox-import-scripts',Key='%s.cyp' % (USECASE))
    queriesString = response['Body'].read()
    
    queries  = queriesString.split(";\n")
    session = get_db_session()
    for query in queries:
      print("###### Executing query:\n%s" % (query))
      results = session.run(query, parameters={})
      for record in results:
        print(record)
    session.close()
  except botocore.exceptions.ClientError as e:
    if e.response['Error']['Code'] == "404":
      print("No import script found for usecase: %s" % (USECASE))
  
import_data()

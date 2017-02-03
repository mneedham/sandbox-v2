from __future__ import print_function
import json
from neo4j.v1 import GraphDatabase, basic_auth, constants
import boto3
import datetime
import time
import os
import sblambda
import urllib2

def request_backup(sandboxIp, sandboxPort, sandboxHashkey):
    req = urllib2.Request(url='http://%s:%s/?sandbox=%s' % (sandboxIp, sandboxPort, sandboxHashkey) )
    f = urllib2.urlopen(req)
    res = f.read()
    return res

def get_sandbox_to_backup(sandboxHashkey):
    session = sblambda.get_db_session()

    instances_query = """
    MATCH 
      (u:User)-[:IS_ALLOCATED]-(s:Sandbox)-[:IS_INSTANCE_OF]-(uc:Usecase)
    WHERE 
      s.sandbox_hash_key = {sandbox_hash_key}
      AND
      s.running=True
    RETURN 
      s.ip AS ip, s.backupPort AS backupPort
    """

    results = session.run(instances_query, parameters={"sandbox_hash_key": sandboxHashkey})
    record = False
    for record in results:
      record = dict((el[0], el[1]) for el in record.items())
    session.close()
    return record

def mark_tasks_stopped(tasks):
    session = sblambda.get_db_session()

    instances_update = """
    UNWIND {tasks} AS task 
    WITH task
    MATCH 
      (u:User)-[:IS_ALLOCATED]-(s:Sandbox)
    WHERE 
      s.taskid = task
    SET
      s.running = false
    """

    results = session.run(instances_update, parameters={"tasks": tasks}).consume()
    session.close()
    return results


def lambda_handler(event, context):
    event_json = json.loads(event["body"])
    sandboxHashkey = event_json['sandboxHashKey']

    body = "{}"
    contentType = 'text/plain'

    print('REQUESTING BACKUP')
    backupInfo = get_sandbox_to_backup(sandboxHashkey)
    
    if backupInfo:
      statusCode = 200
      body = request_backup(backupInfo['ip'], backupInfo['backupPort'], sandboxHashkey)
    else:
      statusCode = 404
      body = '{"error": "couldnt find sandbox by hashkey"}'
 
    return { "statusCode": statusCode, "headers": { "Content-type": contentType, "Access-Control-Allow-Origin": "*" }, "body": body }


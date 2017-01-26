from __future__ import print_function
import json
from neo4j.v1 import GraphDatabase, basic_auth, constants
import boto3
import datetime
import time
import os
import sblambda

SANDBOX_CLUSTER_NAME = os.environ["SANDBOX_CLUSTER_NAME"]

def get_tasks_to_stop(sandboxHashkey):
    session = sblambda.get_db_session()

    instances_query = """
    MATCH 
      (u:User)-[:IS_ALLOCATED]-(s:Sandbox)-[:IS_INSTANCE_OF]-(uc:Usecase)
    WHERE 
      s.sandbox_hash_key = {sandbox_hash_key}
      AND
      s.running=True
    RETURN 
      u.name AS name, s.taskid AS taskid, s.usecase AS usecase, s.ip AS ip, s.port AS port,
      s.sandbox_hash_key AS sandboxHashkey,
      s.boltPort AS boltPort,
      id(s) AS sandboxId,
      uc.model_image AS modelImage
    """

    body = ""
    statusCode = 200
    contentType = 'text/plain'

    results = session.run(instances_query, parameters={"sandbox_hash_key": sandboxHashkey})
    tasks = []
    for record in results:
      record = dict((el[0], el[1]) for el in record.items())
      tasks.append(record["taskid"])
    session.close()
    return tasks

def stop_tasks(tasks, reason):
    global SANDBOX_CLUSTER_NAME
    client = boto3.client('ecs')

    for task in tasks:
        client.stop_task(
            cluster=SANDBOX_CLUSTER_NAME,
            task=task,
            reason=reason)


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
    statusCode = 200
    contentType = 'application/json'

    print('STOPPING TASK')
    tasks = get_tasks_to_stop(sandboxHashkey)
    print(tasks)
    stop_tasks(tasks, 'SandboxStopInstance - requested by user' )
    mark_tasks_stopped(tasks)
 
    return { "statusCode": statusCode, "headers": { "Content-type": contentType, "Access-Control-Allow-Origin": "*" }, "body": body }


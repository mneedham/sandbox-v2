from __future__ import print_function
import json
from neo4j.v1 import GraphDatabase, basic_auth, constants
import boto3
import datetime
import time
import os
import sblambda

    
def get_task_info(taskArray):
    client = boto3.client('ecs')
    response = client.describe_tasks(
        cluster='sandbox-v2',
        tasks=taskArray
    )
    
    containersAndPorts = dict()
    containerInstances = dict()

    for task in response['tasks']:
        taskArn = task['taskArn']
        port = False
        boltPort = False
        backupPort = False

        for container in task['containers']:
            if container['name'] == 'neo4j-enterprise-db-only':
                if 'networkBindings' in container:
                    for binding in container['networkBindings']:
                        if binding['containerPort'] == 7474:
                            port = binding['hostPort']
                        if binding['containerPort'] == 7687:
                            boltPort = binding['hostPort']
                        if binding['containerPort'] == 9500:
                            backupPort = binding['hostPort']

        if taskArn and port:
            containersAndPorts[taskArn] = {"port": port, "boltPort": boltPort, "backupPort": backupPort, "taskArn": task['taskArn'], "containerInstanceArn": task["containerInstanceArn"] }
            containerInstances[ task['containerInstanceArn'] ] = {}
    
    if len(containerInstances) > 0:
        response = client.describe_container_instances(
            cluster='sandbox-v2',
            containerInstances=containerInstances.keys()
        )

        instanceMapping = {}

        for containerInstance in response['containerInstances']:
            print("Instance: %s" % containerInstance['ec2InstanceId'])
            inst = containerInstances[ containerInstance['containerInstanceArn'] ]
            inst['ec2InstanceId'] = containerInstance['ec2InstanceId']
            instanceMapping[ containerInstance['ec2InstanceId'] ] =  containerInstance['containerInstanceArn']

        ec2Client = boto3.client('ec2')
        ec2Instances = ec2Client.describe_instances(InstanceIds=instanceMapping.keys())

        print("All instances: %s" % json.dumps(instanceMapping.keys(), indent=2, cls=sblambda.MyEncoder ))
        print("Number of instances returned: %s" % len(ec2Instances['Reservations'][0]['Instances']))

        for reservation in ec2Instances['Reservations']:
            for instance in reservation['Instances']:
                inst = instance
                ip = inst['PublicIpAddress']
                print("ec2InstanceId for ip: %s" % inst['InstanceId'])
                print("ip: %s" % inst['PublicIpAddress'])
                containerInstances[ instanceMapping[ inst['InstanceId'] ] ]["ip"] = ip 
                containerInstances[ instanceMapping[ inst['InstanceId'] ] ]["ec2InstanceId"] = inst['InstanceId']
   
        for taskArn,containerInfo in containersAndPorts.iteritems(): 
            if 'containerInstanceArn' in containerInfo:
                inst = containerInstances[ containerInfo['containerInstanceArn'] ] 
                print(json.dumps(inst))
                containerInfo['ip'] = inst['ip']
                containerInfo['ec2InstanceId'] = inst['ec2InstanceId']

    return containersAndPorts

def update_db(auth0_key, containersAndPorts):
    session = sblambda.get_db_session()
    
    instances_update = """
    UNWIND {containers} AS c
    WITH c
    MATCH 
      (u:User)-[:IS_ALLOCATED]-(s:Sandbox)
    WHERE 
      u.auth0_key = {auth0_key}
      AND
      s.taskid = c.taskArn
    SET
      s.ip = c.ip,
      s.port = c.port,
      s.boltPort = c.boltPort,
      s.backupPort = c.backupPort
    """
    
    results = session.run(instances_update, parameters={"auth0_key": auth0_key, "containers": containersAndPorts}).consume()

    if session.healthy:
        session.close()
    return results 

def lambda_handler(event, context):
    auth0_key = event['requestContext']['authorizer']['principalId']
    
    session = sblambda.get_db_session()
    
    instances_query = """
    MATCH 
      (u:User)-[:IS_ALLOCATED]-(s:Sandbox)-[:IS_INSTANCE_OF]-(uc:Usecase)
    WHERE 
      u.auth0_key = {auth0_key}
      AND
      s.running=True
    RETURN 
      u.name AS name, s.taskid AS taskid, s.usecase AS usecase, s.ip AS ip, s.port AS port,
      s.boltPort AS boltPort,
      s.backupPort AS backupPort,
      s.password AS password,
      s.expires AS expires,
      s.sandbox_hash_key AS sandboxHashKey,
      s.connection_verified AS connectionVerified,
      id(s) AS sandboxId,
      uc.model_image AS modelImage
    """

    body = ""
    statusCode = 200
    contentType = 'application/json'
    
    results = session.run(instances_query, parameters={"auth0_key": auth0_key})
    resultjson = []
    tasks = []
    for record in results:
      record = dict((el[0], el[1]) for el in record.items())
      if not (record["ip"] and record["boltPort"] and record["backupPort"]):
          tasks.append(record["taskid"])
      else:
          if record["password"]:
              record["password"] = sblambda.decrypt_user_creds(record["password"])
          resultjson.append(record)
          
    if len(tasks) > 0:
        taskInfo = get_task_info(tasks)
        if len(taskInfo) > 0:
            update_db(auth0_key, taskInfo.values())
            
        # re-run DB query to get final data
        results = session.run(instances_query, parameters={"auth0_key": auth0_key})
        for record in results:
          record = dict((el[0], el[1]) for el in record.items())
          if record["password"]:
              record["password"] = sblambda.decrypt_user_creds(record["password"])
          resultjson.append(record)

    # TODO update IPs from taskinfo
    # TODO verify can connect to IP/port
    body = json.dumps(resultjson)
  
    if session.healthy: 
        session.close()
 
    return { "statusCode": statusCode, "headers": { "Content-type": contentType, "Access-Control-Allow-Origin": "*" }, "body": body }

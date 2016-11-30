from __future__ import print_function
import json
from neo4j.v1 import GraphDatabase, basic_auth, constants
import boto3
import datetime
import time
import base64
import os

db_creds = None
DB_HOST = os.environ["DB_HOST"]
DB_CREDS_BUCKET = os.environ["DB_CREDS_BUCKET"]
DB_CREDS_OBJECT = os.environ["DB_CREDS_OBJECT"]

class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return int(time.mktime(obj.timetuple()))

        return json.JSONEncoder.default(self, obj)


def get_db_creds():
    global db_creds, DB_CREDS_BUCKET, DB_CREDS_OBJECT
    
    if db_creds:
        return db_creds
    else:
        s3 = boto3.client('s3')
        kms = boto3.client('kms')
        response = s3.get_object(Bucket=DB_CREDS_BUCKET,Key=DB_CREDS_OBJECT)
        contents = response['Body'].read()
    
        encryptedData = base64.b64decode(contents)
        decryptedResponse = kms.decrypt(CiphertextBlob = encryptedData)
        decryptedData = decryptedResponse['Plaintext']
        db_creds = json.loads(decryptedData)
        return db_creds

def get_db_session():
    creds = get_db_creds()
    driver = GraphDatabase.driver("bolt://%s" % (DB_HOST), auth=basic_auth(creds['user'], creds['password']), encrypted=False)
    session = driver.session()
    return session
    
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

        for container in task['containers']:
            if container['name'] == 'neo4j-enterprise-db-only':
                if 'networkBindings' in container:
                    for binding in container['networkBindings']:
                        if binding['containerPort'] == 7474:
                            port = binding['hostPort']
                        if binding['containerPort'] == 7687:
                            boltPort = binding['hostPort']

        if taskArn and port:
            containersAndPorts[taskArn] = {"port": port, "boltPort": boltPort, "taskArn": task['taskArn'], "containerInstanceArn": task["containerInstanceArn"] }
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

        print("All instances: %s" % json.dumps(instanceMapping.keys(), indent=2, cls=MyEncoder ))
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
    session = get_db_session()
    
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
      s.boltPort = c.boltPort
    """
    
    results = session.run(instances_update, parameters={"auth0_key": auth0_key, "containers": containersAndPorts})
    

def decrypt_user_creds(encryptedPassword):
    kms = boto3.client('kms')
    binaryPassword = base64.b64decode(encryptedPassword)
    return (kms.decrypt(CiphertextBlob=binaryPassword))['Plaintext']


def lambda_handler(event, context):
    auth0_key = event['requestContext']['authorizer']['principalId']
    
    session = get_db_session()
    
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
      s.password AS password,
      id(s) AS sandboxId,
      uc.model_image AS modelImage
    """

    body = ""
    statusCode = 200
    contentType = 'application/json'
    
    results = session.run(instances_query, parameters={"auth0_key": auth0_key})
    tasks = []
    for record in results:
      record = dict((el[0], el[1]) for el in record.items())
      if not (record["ip"] and record["boltPort"]):
          tasks.append(record["taskid"])
          
    if len(tasks) > 0:
        taskInfo = get_task_info(tasks)
        if len(taskInfo) > 0:
            update_db(auth0_key, taskInfo.values())
            
    # re-run DB query to get final data
    results = session.run(instances_query, parameters={"auth0_key": auth0_key})
    resultjson = []
    tasks = []
    for record in results:
      record = dict((el[0], el[1]) for el in record.items())
      if record["password"]:
          record["password"] = decrypt_user_creds(record["password"])
      resultjson.append(record)

    # TODO update IPs from taskinfo
    # TODO verify can connect to IP/port
    body = json.dumps(resultjson)
    
    return { "statusCode": statusCode, "headers": { "Content-type": contentType, "Access-Control-Allow-Origin": "*" }, "body": body }
 

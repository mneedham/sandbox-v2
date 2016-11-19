from __future__ import print_function
import json
from neo4j.v1 import GraphDatabase, basic_auth, constants
import boto3
import datetime
import time
import base64

db_creds = None

class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return int(time.mktime(obj.timetuple()))

        return json.JSONEncoder.default(self, obj)


def get_db_creds():
    global db_creds
    
    if db_creds:
        return db_creds
    else:
        s3 = boto3.client('s3')
        kms = boto3.client('kms')
        response = s3.get_object(Bucket='devrel-lambda-config',Key='neo4j.enc.cfg')
        contents = response['Body'].read()
    
        encryptedData = base64.b64decode(contents)
        decryptedResponse = kms.decrypt(CiphertextBlob = encryptedData)
        decryptedData = decryptedResponse['Plaintext']
        db_creds = json.loads(decryptedData)
        return db_creds

def get_db_session():
    creds = get_db_creds()
    driver = GraphDatabase.driver("bolt://ec2-54-159-226-240.compute-1.amazonaws.com", auth=basic_auth(creds['user'], creds['password']), encrypted=False)
    session = driver.session()
    return session

def get_task_list():
    client = boto3.client('ecs')
    ## TODO: ONLY GETS 100, need to page
    response = client.list_tasks(
        cluster='sandbox-v2',
        desiredStatus='RUNNING'
    )
    # return an array of taskArns
    return response['taskArns']
    
    
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

        for container in task['containers']:
            if container['name'] == 'neo4j-enterprise-db-only':
                if 'networkBindings' in container:
                    for binding in container['networkBindings']:
                        if binding['containerPort'] == 7474:
                            port = binding['hostPort']

        if taskArn and port:
            containersAndPorts[taskArn] = {"port": port, "taskArn": task['taskArn'], "containerInstanceArn": task["containerInstanceArn"] }
            containerInstances[ task['containerInstanceArn'] ] = {}
    
    if len(containerInstances) > 0:
        response = client.describe_container_instances(
            cluster='sandbox-v2',
            containerInstances=containerInstances.keys()
        )

        instanceMapping = {}

        for containerInstance in response['containerInstances']:
            inst = containerInstances[ containerInstance['containerInstanceArn'] ]
            inst['ec2InstanceId'] = containerInstance['ec2InstanceId']
            instanceMapping[ containerInstance['ec2InstanceId'] ] =  containerInstance['containerInstanceArn']

        ec2Client = boto3.client('ec2')
        ec2Instances = ec2Client.describe_instances(InstanceIds=instanceMapping.keys())


        for instance in ec2Instances['Reservations'][0]['Instances']:
            inst = instance
            ip = inst['PublicIpAddress']
            containerInstances[ instanceMapping[ inst['InstanceId'] ] ]["ip"] = ip 
            containerInstances[ instanceMapping[ inst['InstanceId'] ] ]["ec2InstanceId"] = inst['InstanceId']
   
        for taskArn,containerInfo in containersAndPorts.iteritems(): 
            if 'containerInstanceArn' in containerInfo:
                inst = containerInstances[ containerInfo['containerInstanceArn'] ] 
                containerInfo['ip'] = inst['ip']
                containerInfo['ec2InstanceId'] = inst['ec2InstanceId']

    return containersAndPorts

def set_tasks_not_running(tasks):
    session = get_db_session()
    
    instances_update = """
    UNWIND {tasks} AS t
    WITH t
    MATCH 
      (s:Sandbox)
    WHERE 
      s.taskid = t
    SET
      s.running = False
    """
    results = session.run(instances_update, parameters={"tasks": list(tasks)})
    
def stop_tasks(tasks, reason):
    client = boto3.client('ecs')
    
    for task in tasks:
        client.stop_task(
            cluster='sandbox-v2',
            task=task,
            reason=reason)
    
def update_db(containersAndPorts):
    session = get_db_session()
    
    instances_update = """
    UNWIND {containers} AS c
    WITH c
    MATCH 
      (u:User)-[:IS_ALLOCATED]-(s:Sandbox)
    WHERE 
      s.taskid = c.taskArn
    SET
      s.ip = c.ip,
      s.port = c.port
    """
    
    results = session.run(instances_update, parameters={"containers": containersAndPorts})
    

def lambda_handler(event, context):
    session = get_db_session()
   
    ## Find all instances and make sure they have IPs if available 
    instances_query = """
    MATCH 
      (u:User)-[:IS_ALLOCATED]-(s:Sandbox)
    WHERE 
      s.running=True
    RETURN 
      u.name AS name, s.taskid AS taskid, s.usecase AS usecase, s.ip AS ip, s.port AS port
    """

    body = ""
    statusCode = 200
    contentType = 'application/json'
    
    results = session.run(instances_query, parameters={})
    resultjson = []
    tasks = []
    allTasksInDb = set()

    for record in results:
      record = dict((el[0], el[1]) for el in record.items())
      allTasksInDb.add(record["taskid"])
      if not record["ip"]:
          tasks.append(record["taskid"])
      resultjson.append(record)

    allTasksRunning = set(get_task_list())

    print('TASKS IN DB, BUT NOT RUNNING')
    print( allTasksInDb - allTasksRunning )
    set_tasks_not_running( allTasksInDb - allTasksRunning )

    print('TASKS RUNNING, BUT NOT IN DB')
    print( allTasksRunning - allTasksInDb )
    stop_tasks( allTasksRunning - allTasksInDb, 'Task running but not in DB' )
    
    if len(tasks) > 0:
        taskInfo = get_task_info(tasks)
        if len(taskInfo) > 0:
            update_db(taskInfo.values())


    ## Find all tasks and ensure that they're marked as running in DB
  
    return True

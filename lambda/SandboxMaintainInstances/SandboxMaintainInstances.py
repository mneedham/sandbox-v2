from __future__ import print_function
import json
from neo4j.v1 import GraphDatabase, basic_auth, constants
import boto3
import datetime
import time
import os
import sblambda

SANDBOX_CLUSTER_NAME = os.environ["SANDBOX_CLUSTER_NAME"]
ECS_AUTO_SCALING_GROUP_NAME = os.environ["ECS_AUTO_SCALING_GROUP_NAME"]
MEMORY_PER_TASK = int(os.environ["MEMORY_PER_TASK"])
TASKS_AVAILABLE = int(os.environ["TASKS_AVAILABLE"])

def check_utilization():
  global SANDBOX_CLUSTER_NAME, ECS_AUTO_SCALING_GROUP_NAME
  instances = []

  ecs = boto3.client('ecs')
  autos = boto3.client('autoscaling')

  response = ecs.list_container_instances(
    cluster=SANDBOX_CLUSTER_NAME,
    maxResults=100)
  container_instances = response['containerInstanceArns']
  response = ecs.describe_container_instances(
    cluster=SANDBOX_CLUSTER_NAME,
    containerInstances=container_instances)
  for instance in response['containerInstances']:
    remaining_memory = 0
    registered_memory = 0
    for resource in instance['remainingResources']:
      if resource['name'] == 'MEMORY':
        remaining_memory = remaining_memory + resource['integerValue']
    for resource in instance['registeredResources']:
      if resource['name'] == 'MEMORY':
        registered_memory = registered_memory + resource['integerValue']
    instance_description = {
        'arn': instance['containerInstanceArn'],
        'ec2instance': instance['ec2InstanceId'],
        'remaining_memory': remaining_memory,
        'registered_memory': registered_memory,
        'status': instance['status'],
        'runningTasks': instance['runningTasksCount'] }
    instances.append(instance_description)

  total_remaining_memory = 0
  pending_instances = False
  for instance in instances:
    total_remaining_memory = total_remaining_memory + instance['remaining_memory']

  print('TOTAL REMAINING MEMORY: %d' % total_remaining_memory)

  if total_remaining_memory < (MEMORY_PER_TASK * TASKS_AVAILABLE):
    print('NEED MORE INSTANCES')

    asg = autos.describe_auto_scaling_groups(
      AutoScalingGroupNames=[ECS_AUTO_SCALING_GROUP_NAME]
    )
    capacity = asg['AutoScalingGroups'][0]['DesiredCapacity']
   
    autos.set_desired_capacity(
      AutoScalingGroupName=ECS_AUTO_SCALING_GROUP_NAME,
      DesiredCapacity = capacity + 1,
      HonorCooldown = True
    )
    asg = autos.describe_auto_scaling_groups(
      AutoScalingGroupNames=[ECS_AUTO_SCALING_GROUP_NAME]
    )
    capacity = asg['AutoScalingGroups'][0]['DesiredCapacity']
    pp.pprint(capacity)
  elif total_remaining_memory > (2 * (MEMORY_PER_TASK * TASKS_AVAILABLE)):
    print('ATTEMPTING TO TERMINATE INSTANCES')
    terminated_instance = False
    for instance in instances:
      if instance['runningTasks'] == 0 and not terminated_instance and (total_remaining_memory - instance['registered_memory']) > (MEMORY_PER_TASK * TASKS_AVAILABLE):
        print('TERMINATING INSTANCE: %s' % instance['ec2instance'])
        autos.terminate_instance_in_auto_scaling_group(
          InstanceId=instance['ec2instance'],
          ShouldDecrementDesiredCapacity=True)
        terminated_instance = True
  else:
    print('DO NOT NEED MORE INSTANCES')

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

def mark_tasks_for_email():
    session = sblambda.get_db_session()

    instances_update = """
    MATCH 
      (s:Sandbox)
    WHERE 
      s.running = True
      AND
      NOT EXISTS (s.sendEmailReminderOne)
      AND
      s.expires < (timestamp() + 1000 * 60 * 60 * 24 * 3)
    SET
      s.sendEmailReminderOne='Q'
    """
    results = session.run(instances_update).consume()

    return results

def set_tasks_not_running(tasks):
    if len(tasks) > 0:
        session = sblambda.get_db_session()
        
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
        print("Tasks length: %s" % (len(tasks)))
        results = session.run(instances_update, parameters={"tasks": list(tasks)}).consume()
        return results
    else:
        return False
    
def stop_tasks(tasks, reason):
    client = boto3.client('ecs')
    
    for task in tasks:
        client.stop_task(
            cluster='sandbox-v2',
            task=task,
            reason=reason)
    
def update_db(containersAndPorts):
    session = sblambda.get_db_session()
    
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
    
    results = session.run(instances_update, parameters={"containers": containersAndPorts}).consume()
    return results
   
def get_expired_tasks_set():
    session = sblambda.get_db_session()
   
    ## Find all instances and make sure they have IPs if available 
    instances_query = """
    MATCH 
      (u:User)-[:IS_ALLOCATED]-(s:Sandbox)
    WHERE 
      s.running=True
      AND
      timestamp() > s.expires
    RETURN 
      u.name AS name, s.taskid AS taskid, s.usecase AS usecase, s.ip AS ip, s.port AS port
    """

    results = session.run(instances_query)
    resultjson = []
    tasks = []
    expiredTasksInDb = set()

    for record in results:
      record = dict((el[0], el[1]) for el in record.items())
      expiredTasksInDb.add(record["taskid"])
      if not record["ip"]:
          tasks.append(record["taskid"])
      resultjson.append(record)

    return expiredTasksInDb

def get_tasks_in_db_set():
    session = sblambda.get_db_session()
   
    ## Find all instances and make sure they have IPs if available 
    instances_query = """
    MATCH 
      (u:User)-[:IS_ALLOCATED]-(s:Sandbox)
    WHERE 
      s.running=True
    RETURN 
      u.name AS name, s.taskid AS taskid, s.usecase AS usecase, s.ip AS ip, s.port AS port
    """

    results = session.run(instances_query)
    resultjson = []
    tasks = []
    allTasksInDb = set()

    for record in results:
      record = dict((el[0], el[1]) for el in record.items())
      allTasksInDb.add(record["taskid"])
      if not record["ip"]:
          tasks.append(record["taskid"])
      resultjson.append(record)

    return {'allTasksInDb': allTasksInDb,
            'tasksWithoutIp': tasks}



def lambda_handler(event, context):
    body = ""
    statusCode = 200
    contentType = 'application/json'

    tasks = get_tasks_in_db_set()
    allTasksInDb = tasks['allTasksInDb']
    tasksWithoutIp = tasks['tasksWithoutIp']

    allTasksRunning = set(get_task_list())

    expiredTasksInDb = get_expired_tasks_set()

    print('TASKS IN DB, BUT NOT RUNNING')
    print( allTasksInDb - allTasksRunning )
    set_tasks_not_running( allTasksInDb - allTasksRunning )

    print('TASKS RUNNING, BUT NOT IN DB')
    print( allTasksRunning - allTasksInDb )
    stop_tasks( allTasksRunning - allTasksInDb, 'Task running but not in DB' )

    print('EXPIRED TASKS RUNNING')
    print( expiredTasksInDb )
    stop_tasks( expiredTasksInDb, 'Task running in DB but past expiration in DB' )

    print('MARKING TASKS FOR EMAIL REMINDER ONE')
    mark_tasks_for_email()
    
    if len(tasksWithoutIp) > 0:
        taskInfo = get_task_info(tasks)
        if len(taskInfo) > 0:
            update_db(taskInfo.values())
            
    check_utilization()

    session = sblambda.get_db_session() 
    if session.healthy:
        session.close()
 
    return True


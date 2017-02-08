import json
import logging
import boto3
import os
import ast

SANDBOX_CLUSTER_NAME = os.environ["SANDBOX_CLUSTER_NAME"]
LOGGING_LEVEL = int(os.environ["LOGGING_LEVEL"])
AUTOSCALING_GROUP_NAME = os.environ["AUTOSCALING_GROUP_NAME"]

logger = logging.getLogger()
logger.setLevel(LOGGING_LEVEL)

def checkRemoveProtection(containerInstanceArn):
    global SANDBOX_CLUSTER_NAME, AUTOSCALING_GROUP_NAME
    
    ecsClient = boto3.client('ecs')
    tasks = ecsClient.list_tasks(
        cluster=SANDBOX_CLUSTER_NAME,
        containerInstance=containerInstanceArn
    )
    try:
        if len(tasks["taskArns"]) == 0:
            logJson = {
                "status": "REMOVING_PROTECTION_ATTEMPT",
                "containerInstanceArn": containerInstanceArn
            }
            logger.info(json.dumps(logJson))
            containerInstances = ecsClient.describe_container_instances(
                cluster=SANDBOX_CLUSTER_NAME,
                containerInstances=[
                    containerInstanceArn
                ]
            )
            ec2InstanceId = containerInstances['containerInstances'][0]['ec2InstanceId']
            autoScalingClient = boto3.client('autoscaling')
            autoScalingClient.set_instance_protection(
                AutoScalingGroupName=AUTOSCALING_GROUP_NAME,
                InstanceIds=[ec2InstanceId],
                ProtectedFromScaleIn=False
            )
            logJson = {
                "status": "REMOVING_PROTECTION_SUCCESS",
                "containerInstanceArn": containerInstanceArn
            }
            logger.info(json.dumps(logJson))
        else:
            logJson = {
                "status": "CONTAINER_INSTANCE_HAS_TASKS",
                "count": len(tasks["taskArns"]),
                "containerInstanceArn": containerInstanceArn
            }
            logger.info(json.dumps(logJson))
            
    except Exception as e:
        logger.error("Error interogating containerInstanceArn: %s" % containerInstanceArn)
        logger.error(e)
        pass

def checkAddProtection(containerInstanceArn, retry=5):
    global SANDBOX_CLUSTER_NAME, AUTOSCALING_GROUP_NAME
    
    ecsClient = boto3.client('ecs')

    try:
        logJson = {
            "status": "SETTING_PROTECTION_ATTEMPT",
            "containerInstanceArn": containerInstanceArn
        }
        logger.info(json.dumps(logJson))
        containerInstances = ecsClient.describe_container_instances(
            cluster=SANDBOX_CLUSTER_NAME,
            containerInstances=[
                containerInstanceArn
            ]
        )
        ec2InstanceId = containerInstances['containerInstances'][0]['ec2InstanceId']
        autoScalingClient = boto3.client('autoscaling')
        autoScalingClient.set_instance_protection(
            AutoScalingGroupName=AUTOSCALING_GROUP_NAME,
            InstanceIds=[ec2InstanceId],
            ProtectedFromScaleIn=True
        )
        logJson = {
            "status": "SETTING_PROTECTION_SUCCESS",
            "containerInstanceArn": containerInstanceArn
        }
        logger.info(json.dumps(logJson))
        return True
    except Exception as e:
        logger.error("Error setting instance protection on containerInstanceArn: %s" % containerInstanceArn)
        logger.error(e)
        if (retry > 0):
            return checkAddProtection(containerInstanceArn, retry=(retry - 1))
        pass
    return False
    
def lambda_handler(event, context):
    logger.info(json.dumps(event))
    
    try:
        if event["detail-type"] == "ECS Task State Change":
            if event["detail"]["lastStatus"] == "STOPPED":
                logger.info("task stopped - checking to see if other tasks on instance")
                checkRemoveProtection(event["detail"]["containerInstanceArn"])
            if event["detail"]["lastStatus"] == "PENDING" and event["detail"]["desiredStatus"] == "RUNNING":
                checkAddProtection(event["detail"]["containerInstanceArn"])
    except Exception as e:
        logger.debug(e)
        pass
    return True

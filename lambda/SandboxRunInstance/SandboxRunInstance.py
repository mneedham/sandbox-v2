from __future__ import print_function
import json
import boto3
import datetime
import time
import base64
import os
from random_words import RandomWords
from neo4j.v1 import GraphDatabase, basic_auth
import random
import sys
import hashlib


db_creds = None
DB_HOST = os.environ["DB_HOST"]
DB_CREDS_BUCKET = os.environ["DB_CREDS_BUCKET"]
DB_CREDS_OBJECT = os.environ["DB_CREDS_OBJECT"]
SANDBOX_TASK_DEFINITION = os.environ["SANDBOX_TASK_DEFINITION"]
SANDBOX_CLUSTER_NAME = os.environ["SANDBOX_CLUSTER_NAME"]


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return int(time.mktime(obj.timetuple()))

        return json.JSONEncoder.default(self, obj)

def encrypt_user_creds(password):
    kms = boto3.client('kms')
    return base64.b64encode( (kms.encrypt(KeyId='alias/sandbox-neo4j-usercreds', Plaintext=password))['CiphertextBlob']  )

def get_db_creds():
    global db_creds
    global DB_CREDS_BUCKET
    global DB_CREDS_OBJECT
    
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
    global DB_HOST
    
    creds = get_db_creds()
    driver = GraphDatabase.driver("bolt://%s" % (DB_HOST), auth=basic_auth(creds['user'], creds['password']), encrypted=False)
    session = driver.session()
    return session

def get_generated_password():
    rw = RandomWords()
    word = rw.random_words(count=3)
    password = '%s-%s-%s' % (word[0], word[1], word[2])
    return password


def check_sandbox_exists(user, usecase):
    session = get_db_session()
    
    query = """
    MATCH 
      (u:User)-[:IS_ALLOCATED]-(s:Sandbox)
    WHERE 
      u.auth0_key = {auth0_key}
      AND
      s.running=True
      AND
      s.usecase={usecase}
    RETURN
      u.auth0_key
    """
    results = session.run(query, 
      parameters={"auth0_key": user, "usecase": usecase})
    for record in results:
        return True
    return False

def add_sandbox_to_db(user, usecase, taskid, password, sandboxHashKey):
    session = get_db_session()
    
    query = """
    MATCH (uc:Usecase {name: {usecase}})
    MERGE
      (u:User {auth0_key: {auth0_key}})
    CREATE (u)-[:IS_ALLOCATED]->(s:Sandbox)
    SET
      s.running=True,
      s.usecase={usecase},
      s.taskid={taskid},
      s.password={password},
      s.sandbox_hash_key={sandboxHashKey}
    CREATE (s)-[:IS_INSTANCE_OF]->(uc)
    RETURN s
    """
    results = session.run(query,
      parameters={"auth0_key": user, "usecase": usecase, "taskid": taskid, "password": password, "sandboxHashKey": sandboxHashKey})
    
def lambda_handler(event, context):
    global SANDBOX_TASK_DEFINITION, SANDBOX_CLUSTER_NAME
    event_json = json.loads(event["body"])
    usecase = event_json["usecase"]
    user = event['requestContext']['authorizer']['principalId']
    
    if not check_sandbox_exists(user, usecase):
        userDbPassword = get_generated_password()

        # note: this isn't meant to generate a secure random number,
        # just a key used for later lookup
        randomNumber = random.SystemRandom().randint(0, sys.maxint)
        md5 = hashlib.md5()
        md5.update("%s-%s" % (userDbPassword, randomNumber))
        sandboxHashKey = md5.hexdigest()

        client = boto3.client('ecs')
        response = client.run_task(
            cluster=SANDBOX_CLUSTER_NAME,
            taskDefinition=SANDBOX_TASK_DEFINITION,
            overrides={"containerOverrides": [{
                "name": "neo4j-enterprise-db-only",
                "environment":
                    [
                        { "name": "USECASE",
                          "value": usecase},
                        { "name": "EXTENSION_SCRIPT",
                          "value": "extension/extension_script.sh"},
                        { "name": "NEO4J_AUTH",
                          "value": "neo4j/%s" % (userDbPassword)},
                        { "name": "SANDBOX_HASHKEY",
                          "value": "%s" % (sandboxHashKey)}
                    ]
            },
            {
                "name": "neo4j-importer",
                "environment":
                    [
                        { "name": "USECASE",
                          "value": usecase},
                        { "name": "NEO4J_AUTH",
                          "value": "neo4j/%s" % (userDbPassword)}
                    ]
            }
            ]},
            startedBy=('SB("%s","%s")' % (user, usecase))[:36]
        )
        add_sandbox_to_db(user, usecase, response['tasks'][0]['taskArn'], encrypt_user_creds(userDbPassword), sandboxHashKey)

        response_body = json.dumps( { "status": "PENDING",
                          "taskArn": response['tasks'][0]['taskArn'],
                          "password": userDbPassword }, indent=2, cls=MyEncoder )
                          
        # response_body = json.dumps(response['tasks'][0], indent=2, cls=MyEncoder)
        response_statusCode = 200
        response_contentType = 'application/json'
    
        return { "statusCode": response_statusCode, "headers": { "Content-type": response_contentType, "Access-Control-Allow-Origin": "*" }, "body": response_body }
        
    else:
        response_statusCode = 400
        response_contentType = 'application/json'
        response_body = json.dumps( {"errorString": "Sandbox already exists for user: %s and usecase %s"  % (user, usecase) })

        return { "statusCode": response_statusCode, "headers": { "Content-type": response_contentType, "Access-Control-Allow-Origin": "*" }, "body": response_body }


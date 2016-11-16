from __future__ import print_function
import json
import boto3
import datetime
import time
import base64
from neo4j.v1 import GraphDatabase, basic_auth

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

def add_sandbox_to_db(user, usecase, taskid):
    session = get_db_session()
    
    query = """
    MERGE
      (u:User {auth0_key: {auth0_key}})
    CREATE (u)-[:IS_ALLOCATED]->(s:Sandbox)
    SET
      s.running=True,
      s.usecase={usecase},
      s.taskid={taskid}
    RETURN s
    """
    results = session.run(query,
      parameters={"auth0_key": user, "usecase": usecase, "taskid": taskid})
    
def lambda_handler(event, context):
    
    print("Received event: " + json.dumps(event, indent=2, cls=MyEncoder))
    event_json = json.loads(event["body"])
    usecase = event_json["usecase"]
    user = event['requestContext']['authorizer']['principalId']
    
    if not check_sandbox_exists(user, usecase):
        client = boto3.client('ecs')
        response = client.run_task(
            cluster='sandbox-v2',
            taskDefinition='sandbox-with-import:2',
            overrides={"containerOverrides": [{
                "name": "neo4j-enterprise-db-only",
                "environment":
                    [
                        { "name": "USECASE",
                          "value": usecase},
                        { "name": "EXTENSION_SCRIPT",
                          "value": "extension/extension_script.sh"}
                    ]
            }]},
            startedBy='lambdafn'
        )
        add_sandbox_to_db(user, usecase, response['tasks'][0]['taskArn'])

        response_body = json.dumps(response['tasks'][0], indent=2, cls=MyEncoder)
        response_statusCode = 200
        response_contentType = 'application/json'
    
        return { "statusCode": response_statusCode, "headers": { "Content-type": response_contentType, "Access-Control-Allow-Origin": "*" }, "body": response_body }
        
    else:
        response_statusCode = 400
        response_contentType = 'application/json'
        response_body = json.dumps( {"errorString": "Sandbox already exists for user: %s and usecase %s"  % (user, usecase) })

        return { "statusCode": response_statusCode, "headers": { "Content-type": response_contentType, "Access-Control-Allow-Origin": "*" }, "body": response_body }

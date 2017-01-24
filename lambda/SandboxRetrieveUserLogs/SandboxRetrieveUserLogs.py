from __future__ import print_function
import json
import boto3
import os
import base64
from neo4j.v1 import GraphDatabase, basic_auth

db_creds = None
glob_session = None
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
    global glob_session

    if glob_session and glob_session.healthy:
        session = glob_session
    else:
        creds = get_db_creds()
        driver = GraphDatabase.driver("bolt://%s" % (DB_HOST), auth=basic_auth(creds['user'], creds['password']), encrypted=False)
        session = driver.session()
        glob_session = session
    return session

def get_sandbox_by_id(user, sbid):
    session = get_db_session()
    
    query = """
    MATCH 
      (u:User)-[:IS_ALLOCATED]-(s:Sandbox)
    WHERE 
      u.auth0_key = {auth0_key}
      AND
      s.running=True
      AND
      id(s)={sbid}
    RETURN
      s.taskid AS taskid
    """
    results = session.run(query, 
      parameters={"auth0_key": user, "sbid": int(sbid)})
    record = None
    for record in results:
        record = dict((el[0], el[1]) for el in record.items())
    if session.healthy:
        session.close()
    if record:
        return record
    else:
        return False
        
def get_sandbox_by_usecase(user, usecase):
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
      s.taskid AS taskid
    """
    results = session.run(query, 
      parameters={"auth0_key": user, "usecase": usecase})
    record = None
    for record in results:
        record = dict((el[0], el[1]) for el in record.items())
    if session.healthy:
        session.close()
    if record:
        return record
    else:
        return False

def lambda_handler(event, context):
    sbid = None
    usecase = None
    if 'usecase' in event['queryStringParameters']:
        usecase = event['queryStringParameters']['usecase']
    if 'sbid' in event['queryStringParameters']:
        sbid = event['queryStringParameters']['sbid']
    user = event['requestContext']['authorizer']['principalId']
    if sbid:
        record = get_sandbox_by_id(user, sbid)
    else:
        record = get_sandbox_by_usecase(user, usecase)
    if record:
        if ('nextToken' in event['queryStringParameters']):
            nextToken = event['queryStringParameters']['nextToken']
        else:
            nextToken = None
        taskId = record["taskid"]
        taskIdParts = taskId.split(":")
        taskIdInLog = (taskIdParts[5].split("/"))[1]
        client = boto3.client('logs')
        if nextToken:
            events = client.get_log_events(
                logGroupName="neo4j-sandbox",
                logStreamName="neo4j-db/neo4j-enterprise-db-only/%s" % (taskIdInLog),
                nextToken=nextToken
            )
        else:
            events = client.get_log_events(
                logGroupName="neo4j-sandbox",
                logStreamName="neo4j-db/neo4j-enterprise-db-only/%s" % (taskIdInLog)
            )
        response_body = json.dumps(events, indent=2, cls=MyEncoder)
        response_statusCode = 200
        response_contentType = 'application/json'
        return { "statusCode": response_statusCode, "headers": { "Content-type": response_contentType, "Access-Control-Allow-Origin": "*" }, "body": response_body }
    else:
        response_statusCode = 404
        response_body = json.dumps( {"errorString": "Could not find running Sandbox for user: %s and usecase %s"  % (user, usecase) })
        response_contentType = 'application/json'
        return { "statusCode": response_statusCode, "headers": { "Content-type": response_contentType, "Access-Control-Allow-Origin": "*" }, "body": response_body }



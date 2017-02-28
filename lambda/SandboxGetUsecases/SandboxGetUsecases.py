from __future__ import print_function
import json
from neo4j.v1 import GraphDatabase, basic_auth, constants
import boto3
import datetime
import time
import base64
import os
import logging
import traceback

db_creds = None
glob_session = None
DB_HOST = os.environ["DB_HOST"]
DB_CREDS_BUCKET = os.environ["DB_CREDS_BUCKET"]
DB_CREDS_OBJECT = os.environ["DB_CREDS_OBJECT"]
LOGGING_LEVEL = int(os.environ["LOGGING_LEVEL"])


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
    global DB_HOST, glob_session

    if glob_session and glob_session.healthy:
        session = glob_session
    else:
        creds = get_db_creds()
        driver = GraphDatabase.driver("bolt://%s" % (DB_HOST), auth=basic_auth(creds['user'], creds['password']), encrypted=False)
        session = driver.session()
        glob_session = session
    return session

def lambda_handler(event, context):
    global LOGGING_LEVEL
    
    logger = logging.getLogger()
    logger.setLevel(LOGGING_LEVEL)
    
    session = get_db_session()

    if event['requestContext']['stage'] == 'dev':
      enabledStatus = [True,False]
    else:
      enabledStatus = [True]

    try:
      logger.error("QueryString: %s" % (event['queryStringParameters']))
      if 'queryStringParameters' in event and event['queryStringParameters'] and 'additionalUc' in event['queryStringParameters']:
        logger.info("Additional usecases requested: %s" % (json.loads(event['queryStringParameters']['additionalUc'])))
        additionalUc = json.loads(event['queryStringParameters']['additionalUc'])
      else:
        logger.debug("No additional usecases requested: %s" % event['queryStringParameters'])
        additionalUc = []
    except Exception as ex:
      logger.error(traceback.format_exc())
      additionalUc = []
    
    usecases_query = """
    MATCH 
      (uc:Usecase)
    WHERE 
      uc.enabled IN {enabled_status}
      OR
      uc.name IN {additional_uc}
    RETURN 
      uc.name AS name, uc.long_name AS long_name, uc.model_image AS model_image, uc.logo AS logo, uc.description AS description 
    ORDER BY 
      uc.priority DESC
    """

    body = ""
    statusCode = 200
    contentType = 'application/json'
    
    results = session.run(usecases_query, {'enabled_status': enabledStatus, 'additional_uc': additionalUc})
    resultjson = []
    tasks = []
    for record in results:
      record = dict((el[0], el[1]) for el in record.items())
      resultjson.append(record)
    
    body = json.dumps(resultjson)
  
    if session.healthy: 
        session.close() 

    return { "statusCode": statusCode, "headers": { "Content-type": contentType, "Access-Control-Allow-Origin": "*" }, "body": body }

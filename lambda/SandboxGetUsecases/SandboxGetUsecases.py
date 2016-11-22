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
    
def lambda_handler(event, context):
    session = get_db_session()
    
    usecases_query = """
    MATCH 
      (uc:Usecase)
    WHERE 
      uc.enabled=True
    RETURN 
      uc.name AS name, uc.model_image AS model_image, uc.logo AS logo, uc.description AS description 
    """

    body = ""
    statusCode = 200
    contentType = 'application/json'
    
    results = session.run(usecases_query)
    resultjson = []
    tasks = []
    for record in results:
      record = dict((el[0], el[1]) for el in record.items())
      resultjson.append(record)
    
    body = json.dumps(resultjson)
    
    return { "statusCode": statusCode, "headers": { "Content-type": contentType, "Access-Control-Allow-Origin": "*" }, "body": body }

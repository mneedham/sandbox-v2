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
from string import Template

db_creds = None
glob_session = None

DB_HOST = os.environ["DB_HOST"]
DB_CREDS_BUCKET = os.environ["DB_CREDS_BUCKET"]
DB_CREDS_OBJECT = os.environ["DB_CREDS_OBJECT"]
EMAIL_TEMPLATES_BUCKET = os.environ["EMAIL_TEMPLATES_BUCKET"]
SANDBOX_URL = os.environ["SANDBOX_URL"]

class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return int(time.mktime(obj.timetuple()))

        return json.JSONEncoder.default(self, obj)


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
    global DB_HOST, glob_session

    if glob_session and glob_session.healthy:
        session = glob_session
    else:
        creds = get_db_creds()
        driver = GraphDatabase.driver("bolt://%s" % (DB_HOST), auth=basic_auth(creds['user'], creds['password']), encrypted=False)
        session = driver.session()
        glob_session = session
    return session

def get_sandboxes_for_email_reminderone():
    session = get_db_session()

    instances_query = """
    MATCH 
      (uc:Usecase)<-[:IS_INSTANCE_OF]-(s:Sandbox)<-[:IS_ALLOCATED]-(u:User)
    WHERE 
      s.running = True
      AND
      s.sendEmailReminderOne = 'Q'
    RETURN
      s.usecase AS usecase, s.ip, s.port, s.boltPort, s.expires AS expires, id(s) AS id, u.name AS name, u.email AS email, uc.long_name AS uc_long_name
    """
    results = session.run(instances_query)

    sandboxes = []

    for record in results:
      record = dict((el[0], el[1]) for el in record.items())
      sandboxes.append(record)

    if session.healthy:
        session.close()

    return sandboxes

def set_sandboxes_email_status_reminderone(sandbox_ids, status):
    session = get_db_session()

    instances_update_query = """
    MATCH 
      (s:Sandbox)
    WHERE 
      id(s) IN {sandbox_ids}
    SET
      s.sendEmailReminderOne={status}
    """
    results = session.run(instances_update_query, parameters={"sandbox_ids": list(sandbox_ids), "status": status}).consume()

    if session.healthy:
        session.close()

    return results



def send_email_reminderone(sandboxes):
    global SANDBOX_URL

    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=EMAIL_TEMPLATES_BUCKET,Key="%s.txt" % ('reminderone'))
    templatePlainText = response['Body'].read()

    templateObj = Template(templatePlainText)

    print(templatePlainText)

    client = boto3.client('ses')
    for sandbox in sandboxes:
      try:
        dt = datetime.datetime.utcfromtimestamp(int(sandbox['expires']) / 1000)
        expiresStr = "%s GMT" % (dt.strftime("%A, %d. %B %Y %I:%M%p"))

        bodyPlainText = templateObj.substitute(sburl=SANDBOX_URL, greeting=sandbox['name'], expires=expiresStr, usecase=sandbox['uc_long_name'])
        response = client.send_email(
            Source = 'Neo4j DevRel <devrel+sandbox@neo4j.com>',
            SourceArn = 'arn:aws:ses:us-east-1:128916679330:identity/neo4j.com',
            Destination = {
                'ToAddresses': [ sandbox['email'] ]
            },
            Message = {
                'Subject': { 'Data': 'Your New Neo4j Sandbox expires soon - Extend today' },
                'Body': { 'Text': { 'Data': bodyPlainText } }
            }
        )
        print(response)
      except:
        logging.error(traceback.format_exc())


def get_sandboxes_for_email_created():
    session = get_db_session()

    instances_query = """
    MATCH 
      (uc:Usecase)<-[:IS_INSTANCE_OF]-(s:Sandbox)<-[:IS_ALLOCATED]-(u:User)
    WHERE 
      s.running = True
      AND
      s.sendEmailCreated = 'Q'
    RETURN
      s.usecase AS usecase, s.ip, s.port, s.boltPort, s.expires, id(s) AS id, u.name AS name, u.email AS email, uc.long_name AS uc_long_name
    """
    results = session.run(instances_query)

    sandboxes = []

    for record in results:
      record = dict((el[0], el[1]) for el in record.items())
      sandboxes.append(record)

    if session.healthy:
        session.close()

    return sandboxes

def set_sandboxes_email_status_created(sandbox_ids, status):
    session = get_db_session()

    instances_update_query = """
    MATCH 
      (s:Sandbox)
    WHERE 
      id(s) IN {sandbox_ids}
    SET
      s.sendEmailCreated={status}
    """
    results = session.run(instances_update_query, parameters={"sandbox_ids": list(sandbox_ids), "status": status}).consume()

    if session.healthy:
        session.close()

    return results



def send_email_created(sandboxes):
    global SANDBOX_URL

    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=EMAIL_TEMPLATES_BUCKET,Key="%s.txt" % ('created'))
    templatePlainText = response['Body'].read()
    
    templateObj = Template(templatePlainText)
    
    print(templatePlainText)
    
    client = boto3.client('ses')
    for sandbox in sandboxes:
      try:
        bodyPlainText = templateObj.substitute(sburl=SANDBOX_URL, greeting=sandbox['name'])
        response = client.send_email(
            Source = 'Neo4j DevRel <devrel+sandbox@neo4j.com>',
            SourceArn = 'arn:aws:ses:us-east-1:128916679330:identity/neo4j.com',
            Destination = {
                'ToAddresses': [ sandbox['email'] ]
            },
            Message = {
                'Subject': { 'Data': 'You\'ve Created a New Neo4j Sandbox for %s' % (sandbox['uc_long_name']) },
                'Body': { 'Text': { 'Data': bodyPlainText } }
            }
        )
        print(response)
      except:
        logging.error(traceback.format_exc())





def lambda_handler(event, context):
    body = ""
    statusCode = 200
    contentType = 'application/json'

    status = 'S'


    try:
      sbs = get_sandboxes_for_email_reminderone()
      # don't actually send this email yet
      send_email_reminderone(sbs)
    except:
      logging.error(traceback.format_exc())
      print('Error in sending email -setting status as M')
      status = 'M'

    try:
      sbids = []
      for sb in sbs:
        sbids.append(sb['id'])
      set_sandboxes_email_status_reminderone(sbids, status)
    except Exception as e:
      logging.error(traceback.format_exc())
      print('Error in setting sandbox statuses')

    print('SANDBOXES FOR EMAIL REMINDER ONE')
    print( sbs )
    
    
    try:
      sbs = get_sandboxes_for_email_created()
      send_email_created(sbs)
    except:
      logging.error(traceback.format_exc())
      print('Error in sending email -setting status as M')
      status = 'M'

    try:
      sbids = []
      for sb in sbs:
        sbids.append(sb['id'])
      set_sandboxes_email_status_created(sbids, status)
    except Exception as e:
      logging.error(traceback.format_exc())
      print('Error in setting sandbox statuses')

    print('SANDBOXES FOR EMAIL CREATED')
    print( sbs )
  
    return True

from __future__ import print_function
import json
from neo4j.v1 import GraphDatabase, basic_auth, constants
import boto3
import datetime
import time
import os
import sblambda
import urllib2
import logging

LOGGING_LEVEL = int(os.environ["LOGGING_LEVEL"])
EXTEND_LENGTH_DAYS = int(os.environ['EXTEND_LENGTH_DAYS'])

logger = logging.getLogger()
logger.setLevel(LOGGING_LEVEL)

def add_user_profile_response(user,formObj):
    session = sblambda.get_db_session()

    instances_update = """
    WITH {formObj} AS form
    MATCH (u:User {auth0_key:{user}})
    CREATE (l:LeadForm)
    SET
      l.email=form.email,
      l.company=form.company,
      l.country=form.country,
      l.industry=form.industry,
      l.telephone=form.telephone,
      l.jobrole=form.jobrole,
      l.whyneo4j=form.whyneo4j,
      l.submitted=timestamp()
    CREATE (u)-[:SUBMITTED_FORM]->(l)
    """
    results = session.run(instances_update, parameters={"user": user, "formObj": formObj})
    for record in results:
        return True
    return False


def grant_extension(user, days):
    session = sblambda.get_db_session()

    instances_update = """
    MATCH 
      (u:User)-[:IS_ALLOCATED]-(s:Sandbox)
    WHERE 
      u.auth0_key = {user}
      AND
      s.running = true
    SET
      s.expires = s.expires + (1000 * 60 * 60 * 24 * {days})
    RETURN
      s.sandbox_hash_key AS sandboxHashKey, s.expires AS expires
    """

    results = session.run(instances_update, parameters={"user": user, "days": days})
    for record in results:
        return True
    return False

def lambda_handler(event, context):
    global EXTEND_LENGTH_DAYS, logger

    formObj = json.loads(event["body"])
    user = event['requestContext']['authorizer']['principalId']

    add_user_profile_response(user, formObj)

    bodyObj = {}
    contentType = 'text/javascript'

    logger.info('REQUESTING EXTENSION for user: %s and length: %s days' % (user, EXTEND_LENGTH_DAYS))

    if (grant_extension(user, EXTEND_LENGTH_DAYS)):
      statusCode = 200
      bodyObj['status'] = 'SUCCESS';
      bodyObj['extendedByDays'] = EXTEND_LENGTH_DAYS;
      logger.info('SUCCESS GRANTING EXTENSION for user: %s and length: %s days' % (user, EXTEND_LENGTH_DAYS))
    else:
      statusCode = 500
      bodyObj['status'] = 'FAIL'
      bodyObj['error'] = 'couldnt extend sandboxes'
 
    return { "statusCode": statusCode, "headers": { "Content-type": contentType, "Access-Control-Allow-Origin": "*" }, "body": json.dumps(bodyObj) }


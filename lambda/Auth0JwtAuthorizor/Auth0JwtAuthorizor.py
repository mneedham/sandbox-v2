from __future__ import print_function
import json
import os
import jwt
import base64
import re
import urllib2
import boto3
from neo4j.v1 import GraphDatabase, basic_auth, constants
import logging
import sblambda
from awspol import AuthPolicy, HttpVerb
import ast

logger = None

if 'LOGGING_LEVEL' in os.environ:
  LOGGING_LEVEL = int(os.environ["LOGGING_LEVEL"])
else:
  LOGGING_LEVEL = 30

if 'REVALIDATE_USER' in os.environ:
  REVALIDATE_USER = ast.literal_eval(os.environ["REVALIDATE_USER"])
else:
  REVALIDATE_USER = True

logger = logging.getLogger()
logger.setLevel(LOGGING_LEVEL)

def add_update_user(user, jwt):
    global REVALIDATE_USER

    data = { "id_token": jwt }

    profile = {}
    name = '<default>'
    email = '<default>'
    picture = '<default>'
    email = '<default>'
    description = '<default>'
    emailVerified = True

    try:
      req = urllib2.Request(
          	url = 'https://neo4j-sandbox.auth0.com/tokeninfo',
          	headers = {"Content-type": "application/json"},
  	        data = json.dumps(data))
        
      f = urllib2.urlopen(url = req)
      jsonProfile = f.read()
      profile = json.loads(jsonProfile)
      logger.debug(jsonProfile)

    except urllib2.HTTPError as h:
      if REVALIDATE_USER:
        raise
      else:
        name = 'UNVALIDATED USER'
        description = 'UNVALIDATED USER: SHOULD ONLY SEE IN TEST'
        logger.warning('Allowing unvalidated user to proceed (REVALIDATE_USER=%s). User: "%s"' % (REVALIDATE_USER, user))
        pass
    
    
    if 'name' in profile:
        name = profile['name']

    if 'picture' in profile:
        picture = profile['picture']
        
    if 'description' in profile:
        description = profile['description']

    if 'email' in profile:
        email = profile['email']

    if 'email_verified' in profile:
        if profile['email_verified'] == False:
          emailVerified = False
    

    query = """
    MERGE
      (u:User {auth0_key: {auth0_key}})
    SET
      u.name={name},
      u.picture={picture},
      u.description={description},
      u.email={email},
      u.email_verified={emailVerified}
    RETURN u
    """
    session = sblambda.get_db_session()
    session.run(query,
      parameters={"auth0_key": user, "name": name, "picture": picture, "description": description, "email": email, "emailVerified": emailVerified}).consume()
    
    if session.healthy: 
        session.close() 

    return True


def lambda_handler(event, context):
    global LOGGING_LEVEL, logger


    creds = sblambda.get_creds('auth0')
    secret = creds['auth0_secret']
    encoded = event['authorizationToken']

    # TODO Handle expired signatures 
    # https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/lambda/Auth0JwtAuthorizor;stream=2017/01/23/%5B$LATEST%5D04afd1c304614be18654a7972aa6e935

    try:
      decoded = jwt.decode(encoded, secret, algorithms=['HS256'], audience=creds['auth0_audience'])
   
      # don't skip adding user on read only 
      # if re.search("SandboxRunInstance$", event['methodArn']):
      add_update_user(decoded['sub'], encoded)    

      tmp = event['methodArn'].split(':')
      apiGatewayArnTmp = tmp[5].split('/')
      awsAccountId = tmp[4]

      principalId = decoded['sub']

      policy = AuthPolicy(principalId, awsAccountId)
      policy.restApiId = apiGatewayArnTmp[0]
      policy.region = tmp[3]
      policy.stage = apiGatewayArnTmp[1]
#    policy.denyAllMethods()
      policy.allowMethod(HttpVerb.GET, 'SandboxGetRunningInstancesForUser')
      policy.allowMethod(HttpVerb.GET, 'SandboxRetrieveUserLogs')
      policy.allowMethod(HttpVerb.POST, 'SandboxRunInstance')
      policy.allowMethod(HttpVerb.POST, 'SandboxStopInstance')
      policy.allowMethod(HttpVerb.POST, 'SandboxBackupInstance')
      policy.allowMethod(HttpVerb.POST, 'SandboxExtend')
    except jwt.ExpiredSignatureError:
      logger.info('JWT token denied because expired')
      raise Exception('Unauthorized')

    # Finally, build the policy and exit the function using return
    return policy.build()


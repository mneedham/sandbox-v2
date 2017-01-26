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

if 'LOGGING_LEVEL' in os.environ:
  LOGGING_LEVEL = int(os.environ["LOGGING_LEVEL"])
else:
  LOGGING_LEVEL = 30

def add_update_user(user, jwt):
    session = sblambda.get_db_session()

    data = { "id_token": jwt }

    req = urllib2.Request(
        	url = 'https://neo4j-sync.auth0.com/tokeninfo',
        	headers = {"Content-type": "application/json"},
	        data = json.dumps(data))
        
    f = urllib2.urlopen(url = req)
    profile = json.loads(f.read())
    
    name = ''
    picture = ''
    email = 'none'
    description = ''
    
    if 'name' in profile:
        name = profile['name']

    if 'picture' in profile:
        picture = profile['picture']
        
    if 'description' in profile:
        description = profile['description']

    query = """
    MERGE
      (u:User {auth0_key: {auth0_key}})
    SET
      u.name={name},
      u.picture={picture},
      u.description={description}
    RETURN u
    """
    results = session.run(query,
      parameters={"auth0_key": user, "name": name, "picture": picture, "description": description}).consume()
    
    if session.healthy: 
        session.close() 

    return results


def lambda_handler(event, context):
    global LOGGING_LEVEL

    logger = logging.getLogger()
    logger.setLevel(LOGGING_LEVEL)

    creds = sblambda.get_creds('auth0')
    secret = base64.b64decode(creds['auth0_secret'])
    encoded = event['authorizationToken']

    # TODO Handle expired signatures 
    # https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/lambda/Auth0JwtAuthorizor;stream=2017/01/23/%5B$LATEST%5D04afd1c304614be18654a7972aa6e935

    try:
      decoded = jwt.decode(encoded, secret, algorithms=['HS256'], audience=creds['auth0_audience'])
    
      if re.search("SandboxRunInstance$", event['methodArn']):
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
    except jwt.ExpiredSignatureError:
      logger.error('JWT token denied because expired')
      raise Exception('Unauthorized')

    # Finally, build the policy and exit the function using return
    return policy.build()


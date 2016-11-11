from __future__ import print_function
import json
from neo4j.v1 import GraphDatabase, basic_auth, constants

def lambda_handler(event, context):
    driver = GraphDatabase.driver("bolt://ec2-54-159-226-240.compute-1.amazonaws.com", auth=basic_auth("neo4j", "g1HYDlUi$Dp0fRo%2JJI"), encrypted=False)
    session = driver.session()

    auth0_key = event['auth0_key']
    
    instances_query = """
    MATCH 
      (u:User)-[:IS_ALLOCATED]-(s:Sandbox)
    WHERE 
      u.auth0_key = {auth0_key}
      AND
      s.running=True
    RETURN 
      u.name AS name, s.taskid AS taskid, s.usecase AS usecase
    """

    results = session.run(instances_query, parameters={"auth0_key": auth0_key})
    for record in results:
      return dict((el[0], el[1]) for el in record.items())
#      return record.items()
#      return { 'name': record['name'], 'taskid': record['taskid'], 'usecase': record['usecase'] }

    #print("Received event: " + json.dumps(event, indent=2))
    #raise Exception('Something went wrong')



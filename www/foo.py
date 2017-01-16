# pip install neo4j-driver

from neo4j.v1 import GraphDatabase, basic_auth

driver = GraphDatabase.driver(
    "bolt://54.84.149.149:32820", 
    auth=basic_auth("neo4j", "stations-insertions-ports"))
session = driver.session()

cypher_query = '''
MATCH (c:Candidate)
RETURN c.name AS name
WHERE c.party = {party}
LIMIT 10
'''

results = session.run(cypher_query,
  parameters={"party": "Republican"})

for record in results:
  print(record['name'])


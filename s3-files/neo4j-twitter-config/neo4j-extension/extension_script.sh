#! /bin/bash

cp /conf-base/neo4j.conf $PWD/conf/neo4j.conf
echo "browser.post_connect_cmd=play http://guides.neo4j.com/sandbox/$USECASE" >> $PWD/conf/neo4j.conf
echo "dbms.connector.bolt.advertised_address=`curl -s \"https://ppriuj7e7i.execute-api.us-east-1.amazonaws.com/prod/SandboxGetInstanceByHashKey?sandboxHashKey=$SANDBOX_HASHKEY\"`" >> $PWD/conf/neo4j.conf
python /backup-server.py &

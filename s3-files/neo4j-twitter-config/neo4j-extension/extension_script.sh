#! /bin/bash

cp /conf-base/neo4j.conf $PWD/conf/neo4j.conf
cp -R /conf-base/certs $PWD/conf/

if [ -d "/usecase-datastores-ro/$USECASE.db" ]; then
  cp -R /usecase-datastores-ro/$USECASE.db $PWD/data/databases/
 echo "dbms.active_database=$USECASE.db" >> $PWD/conf/neo4j.conf
fi

echo "browser.post_connect_cmd=play https://neo4jsandbox.com/guides/$USECASE/" >> $PWD/conf/neo4j.conf
echo "dbms.connector.bolt.advertised_address=`curl -s \"https://ppriuj7e7i.execute-api.us-east-1.amazonaws.com/prod/SandboxGetInstanceByHashKey?sandboxHashKey=$SANDBOX_HASHKEY\"`" >> $PWD/conf/neo4j.conf
python /backup-server.py &

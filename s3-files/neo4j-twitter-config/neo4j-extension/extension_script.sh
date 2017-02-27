#!/bin/bash

cp /conf-base/neo4j.conf $PWD/conf/neo4j.conf
cp -R /conf-base/certs $PWD/conf/

if [ -d "/usecase-datastores-ro/$USECASE.db" ]; then
  cp -R /usecase-datastores-ro/$USECASE.db $PWD/data/databases/
 echo "dbms.active_database=$USECASE.db" >> $PWD/conf/neo4j.conf
fi

echo "browser.post_connect_cmd=play https://neo4jsandbox.com/guides/$USECASE/" >> $PWD/conf/neo4j.conf

TRYCOUNT=5
IP_SUCCESS=false

while [ $TRYCOUNT -gt 0 ]; do
    let "TRYCOUNT = TRYCOUNT-1"
    resp=`curl -fs "https://ppriuj7e7i.execute-api.us-east-1.amazonaws.com/prod/SandboxGetInstanceByHashKey?sandboxHashKey=$SANDBOX_HASHKEY"`
    if [ $? -eq 0 ]; then
        TRYCOUNT=0
        IP_SUCCESS=true
    else
        IP_SUCCESS=false
        sleep 2
    fi
done

if [ $IP_SUCCESS == true ]; then
  echo "IP_SUCCESS: Setting IP/port for bolt to: $resp"
  echo "dbms.connector.bolt.advertised_address=$resp" >> $PWD/conf/neo4j.conf
  python /backup-server.py &
else
  echo "ERROR: Failed to retrieve IP/port combination for bolt from SandboxGetInstanceByHashKey"
  exit 1
fi

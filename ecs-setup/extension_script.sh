#! /bin/bash

cp /conf-base/neo4j.conf $PWD/conf/neo4j.conf
echo "browser.post_connect_cmd=play $USECASE" >> $PWD/conf/neo4j.conf

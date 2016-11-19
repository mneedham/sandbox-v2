#! /bin/bash

cp /conf-base/neo4j.conf $PWD/conf/neo4j.conf
echo "browser.post_connect_cmd=play http://guides.neo4j.com/sandbox/$USECASE" >> $PWD/conf/neo4j.conf

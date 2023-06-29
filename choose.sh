#!/bin/bash

export PATH="/usr/bin:$PATH"

if dmidecode -s system-product-name | grep -q "Raspberry"; then

  echo "server"
  FILE="server.py"
  FILE_PATH="server/server_3.2.py"
  DOCKER_PATH="/app/server.py"
  DOCKER_TAG="ledserver"
  REQ="RPi.GPIO paho-mqtt"

else

  echo "client"
  FILE="client.py"
  FILE_PATH="client/client_3.2.py"
  DOCKER_PATH="/app/client.py"
  DOCKER_TAG="ledclient"
  REQ="paho-mqtt"

fi


echo -e "FROM python:3.9\n\nCOPY $FILE_PATH $DOCKER_PATH\n\nWORKDIR /app\n\nRUN pip install $REQ\n\nEXPOSE 1883\n\nCMD python3 $FILE" > Dockerfile 

docker build --rm -t $DOCKER_TAG . ;

docker run -it -p 8883:1883 $DOCKER_TAG ;
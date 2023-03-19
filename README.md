# C-S_RasPi_Led
Client server app running on terminal developed in python using tcp communication with paho.mqtt.client as mqtt. 

local broker: mosquitto.
libraries imported: random, threading, time, RPi.GPIO

The app enable the server to operate from terminal by itself or to connect with other clients and execute the given commands.
To connect with a client, the server can dispose the communication as open and wait for clients to log in with a password setted by the server itself.
The server can manage the connection of maximum 2 clients together, deciding if to open or close the communication, or to disconnect from a specific choosen client.

Enabeling the commented lines, it's possible to led on or off 2 leds attached to the server machine on pin 18 and 19.

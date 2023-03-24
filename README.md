# C-S_RasPi_Led
Client server app to control 2 leds connected to a raspberry pi (on pin 18 and 19).
Communication between client and server is built over tcp (socket or mqtt).
The app is using a local mqtt broker: the communication between client and server can function inside a local connection.
To enable the communication outside of the LAN it is possible touse a non-local broker and to create a ngrok tunnel for the socket.
Comment linet to simplify the integration of internet connections and operate directly on the leds still need to be implemented.

# Server side
The server script has to run on a raspberryPi or a device pinned to some leds.
The current version WILL NOT led on or off any led, but the structure lets this function to be enabled and functioning as the GPIO commented lines get activated.
From the server side is possible to operate on the leds as well as receve command from a maximum number of 2 clients at a time; The server won't accept any more client.

# Client side
The client script can run on almost any device and needs the autentication password setted by the server to be able to build a channel of communication stable.
The client is able to connect with the server using socket or mqtt by choice.

# C-S_RasPi_Led
Client server app to control 2 leds connected to a raspberry pi (on pin 18 and 19).
To enable operations on the leds, GPIO lines need to be decommented, otherwise client and server will only exchange messages.

Communication between client and server is built over tcp (socket or mqtt).
The application can manage communication between client and server inside or outside local network.
To enable the communication via socket outside of the LAN it is necessary to tunnel via ngrok

# Server side
The server script has to run on a raspberryPi or a device pinned to some leds.
The default version WILL NOT led on or off any led, but the structure lets this function to be enabled and functioning as the GPIO commented lines get activated.
From the server side is possible to operate on the leds as well as receve command from a maximum number of 2 clients at a time to do that; The server won't accept any more client.

# Client side
The client script can run on almost any device and needs the autentication password setted by the server to be able to build a channel of communication stable.
The client is able to connect with the server using socket or mqtt by choice.

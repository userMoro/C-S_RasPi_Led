# C-S_RasPi_Led
Client server app to control 2 leds connected to a raspberry pi (on pin 18 and 19). The leds are turned on/of from the server of from max 2 clients at the same time. Communication between client and server is built over tcp (ngrok/socket or mqtt). It is necessary to start a ngrok tunnel to communicate using socket.

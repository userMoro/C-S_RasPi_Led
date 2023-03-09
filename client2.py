import funzioniC
import paho.mqtt.client as mqtt
import random
import socket
import pickle


def defusername():
    while True:
        username=input("inserisci username: ")
        if username=="":
            print("\nimposta uno username prima di iniziare\n")
            continue
        else:
            break
    num=random.randint(0,9)
    username=username+"-"+str(num)
    print("\nciao", username,"\n")
    return username


def setupmqtt():
    broker_url = "mqtt.eclipseprojects.io"
    broker_port = 1883

    def on_connect(client, userdata, flags, rc):
        print("Connected to broker")

    c = mqtt.Client(username)
    c.on_connect = on_connect
    c.connect(broker_url,broker_port)
    c.subscribe("led/aut/rensp")
    c.loop()
    return c




username=defusername()
while True:
    mod=input("1 = connessione via ngrok/socket\n2 = connessione via mqtt\n3 = esci\n")
    if mod =="1":
        client_socket, host, port=funzioniC.setupconnection()
        client_socket.settimeout(10)
        try:
            client_socket.connect((host,port))
        except socket.gaierror:
            client_socket.close()
            print("\nporta/url inseriti non validi\n")
            continue
        try:
            password=client_socket.recv(1024).decode('utf-8')
            if not password:
                client_socket.close()
                print("\nserver non in linea o pieno; Timeout\n")
                continue
        except TimeoutError:
            client_socket.close()
            print("\nserver non in linea o pieno; Timeout\n")
            continue
        print("\n")
        conferma=False
        for i in range(3):
            print("tentativo",i+1,"su 3")
            auth=input("inserisci password: ")
            if password==auth:
                tupla=("                    connesso",username)
                ser_tupla = pickle.dumps(tupla)
                client_socket.send(ser_tupla)
                conferma=True
                break
            else:
                print("\npassword errata\n")
        if i==2 and conferma==False:
            tupla=("autenticazione fallita",username)
            ser_tupla = pickle.dumps(tupla)
            client_socket.send(ser_tupla)
            client_socket.close()
            continue
        print("\n..in connessione..\n")
        funzioniC.controlloremoto(client_socket)
        client_socket.close()
        continue
        
    elif mod=="2":
        autmqtt=""
        def on_message(client, userdata, message):
            global autmqtt
            autmqtt = message.payload.decode("utf-8")
            print("Received message:", autmqtt)
            global message_received
            message_received = True

        client = setupmqtt()
        client.subscribe("led/aut/spam", qos=2)
        client.on_message = on_message
        client.loop_start()

        message_received = False
        while not message_received:
            pass
        client.unsubscribe("led/aut/spam")
        client.loop_stop()

        passmqtt = input("inserisci password: ")
        if autmqtt == passmqtt:
            print("ok")
            topiclient="led/"+username
            print(topiclient)
            client.publish("led/aut/rensp", topiclient, qos=2)
        else:
            print("ko")
            client.publish("led/aut/rensp", "ko", qos=2)

        client.loop_stop()

    elif mod=="3":
        break
    else:
        print("\ninserisci un dato valido\n")
        continue

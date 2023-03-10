#import RPi.GPIO as GPIO
#GPIO.setmode(GPIO.BCM)
#GPIO.setup(18, GPIO.OUT)
#GPIO.setup(19, GPIO.OUT)
import socket
import paho.mqtt.client as mqtt

def terminal():
    while True:
        on_off=input("inserisci un comando:\n-on1 = accendi led 1\n-on2 = accendi led 2\n-off1 = spegni led 1\n-off2 = spegni led 2\n-back = seleziona modalità\n")
        if on_off=="on1":
            GPIO.output(18, True)
        elif on_off=="on2":
            GPIO.output(19, True)
        elif on_off=="off1":
            GPIO.output(18, False)
        elif on_off=="off2":
            GPIO.output(19, False)
        elif on_off=="back":
            break
        else:
            print("\ndato inserito non valido\n")

def socketsetup():
    host='localhost'                         
    port=5902
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    print("socket creato(host:",host," porta:",port,")")
    s.listen(2)
    return s

def mqttsetup():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Server connesso a broker MQTT")
        else:
            print(f"Errore di connessione. Codice di ritorno: {rc}")
        client.loop_stop()

    broker_url = "mqtt.eclipseprojects.io"
    broker_port = 1883
    c = mqtt.Client("server")
    c.connect(broker_url, broker_port)
    c.on_connect = on_connect
    c.loop_start()
    return c

def setup():
    socket=socketsetup()
#    mqtt=mqttsetup()
    return socket, mqtt




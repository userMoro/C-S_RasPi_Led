'''
MQTT:
-installare mosquitto 
-id client e server con numeri random 0-1000

-server sottoscritto a topic1/#
-client sottoscritto a rensp/idclient
-client pubblica su topic1/idclient password inserita->server riceve su topic1/# e ricava idclient
-server controlla password: se giusta pubblica ok su rensp/idclient
                                si sottoscrive a comm/idclient->riceve messaggi da client e elabora->se riceve back/timeout si desottoscrive da comm/idclient
                            se sbagliata pubblica ko su rensp/idclient
-client riceve risposta: se ok inizia a pubblicare su comm/idclient
                         se ko chiede di rimandare messaggio fino a 3 volte
                            se 3 ko desottoscrive da rensp/idclient
'''

import random, socket, pickle, threading, time
import paho.mqtt.client as mqtt

#-----------------------MAINCODE FUNCTIONS-----------------------------------   

def inizio():
    while True:
        username=input("inserisci username: ")
        if username=="":
            print("\nimposta uno username prima di iniziare\n")
            continue
        else:
            break
    num=random.randint(0,999)
    username=username+str(num)
    print("\nciao", username,"\n")
    return username

def topics_setup(id):
    rensp="rensp/"+id
    tp1="topic1/"+id
    return rensp, tp1

#-------------------------MQTT FUNCTIONS-------------------------------------

def timeout_timer():
    global start_main_loop, tic, timerblock, pause, stop_spam
    while True:
        tic=time.time()
        while not timerblock:
            toc=time.time()
            if toc-tic>120:
                print("\ntimeout. premi invio\n")
                client.loop_stop()
                client.disconnect()
                start_main_loop=True
                timerblock=True
                stop_spam=True
                if T_comandi.is_alive():
                    pause=True
                break

def heartbeat():
    global start_main_loop, alive, pause, timerblock
    while True:
        alive=time.time()
        while not pause:
            toc=time.time()
            if toc-alive>10:
                print("\nconnessione persa. premi invio\n")
                client.publish(make,sure)
                client.loop_stop()
                client.disconnect()
                start_main_loop=True
                pause=True
                timerblock=True
                break

def comandi_mqtt():
    global pause, start_main_loop, timerblock, tic
    commtopic="comm/"+username
    while True:
        while not pause:
            on_off=input("1 = on\n2 = off\n3 = back\n")
            if on_off=="1":
                tic=time.time()
                on_off_mess=on_off+"."+username
                client.publish(commtopic, on_off_mess)
            elif on_off=="2":
                tic=time.time()
                on_off_mess=on_off+"."+username
                client.publish(commtopic, on_off_mess)
            elif on_off=="3":
                on_off_mess=on_off+"."+username
                client.publish(commtopic, on_off_mess)
                client.loop_stop()
                client.disconnect()
                pause=True
                start_main_loop=True
                timerblock=True
                break
            else:
                print("\ndato inserito non valido\n")
                tic=time.time()

def spam(t,p):
    time.sleep(3)
    while not stop_spam:
        client.publish(t,p)
        time.sleep(3)

#------------------------------MAINCODE--------------------------------------

username=inizio()
rensptopic, topic1=topics_setup(username)
make="comm/"+username
sure="3."+username
start_main_loop=True
T_timer=threading.Thread(target=timeout_timer, daemon=True)
timerblock=False
T_comandi=threading.Thread(target=comandi_mqtt, daemon=True)
pause=False
T_beat=threading.Thread(target=heartbeat, daemon=True)

while True:   
    if start_main_loop==True:
        stop_spam=False
        aut_count=2
        mod=input("1 = connessione via ngrok/socket\n2 = connessione via mqtt\n3 = esci\n")
        if mod =="1":
            pass
        elif mod=="2":

            def on_connect(client, userdata, flags, rc): 
                global start_main_loop, tic, timerblock
                start_main_loop=False
                try:
                    T_timer.start()
                except:
                    timerblock=False
                pw=input("inserisci password: ")+"."+username
                tic=time.time()
                client.publish(topic1,pw)
                print("...in attesa del server, non premere pulsanti...")
                threading.Thread(target=spam, args=(topic1,pw)).start()

            def on_message(client, userdata, message):
                global tic, aut_count, start_main_loop, alive, pause, timerblock, stop_spam
                stop_spam=True
                rensp=message.payload.decode()
                if rensp=="ok":
                    try:
                        T_comandi.start()
                        T_beat.start()
                    except:
                        pause=False
                    pass
                elif rensp=="ko":
                    if not aut_count:
                        print("\npassword errata. tentativi esauriti.\n")
                        client.publish(make,sure)
                        client.loop_stop()
                        client.disconnect()
                        timerblock=True
                        start_main_loop=True
                    else:
                        print("\npassword errata.",aut_count,"tentativi rimasti")
                        retry=input("password: ")+"."+username
                        tic=time.time()
                        client.publish(topic1,retry)
                        aut_count-=1
                elif rensp=="beat":
                    alive=time.time()
                pass

            broker_host = "localhost"
            broker_port = 1883
            client = mqtt.Client(username)
            client.connect(broker_host, broker_port)
            client.subscribe(rensptopic)
            client.on_connect = on_connect
            client.on_message = on_message
            client.loop_start()
            time.sleep(1)

        elif mod=="3":
            break
        else:
            print("\ncomando inserito non valido\n")
            continue

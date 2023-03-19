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


#import RPi.GPIO as GPIO
import threading, socket, pickle, time, random, queue
import paho.mqtt.client as mqtt

#----------------------MAINCODE FUNCTIONS-----------------------------------            

def inizio():
    #conn_count=0
    conn_state="chiusa)"
    act_count=0
    name="Server"+str(random.randint(1,999))
    while True:
        passw=input("inserisci password di questo server: ")
        if passw=="":
            print("\nimposta una password prima di iniziare\n")
            continue
        else:
            break
    #return conn_count, act_count, passw, name
    return conn_state, act_count, passw, name

def terminal():
    while True:
        on_off=input("inserisci un comando:\n-on1 = accendi led 1\n-on2 = accendi led 2\n-off1 = spegni led 1\n-off2 = spegni led 2\n-back = seleziona modalità\n")
        if on_off=="on1":
            #GPIO.output(18, True)
            print("GPIO.output(18, True)")
        elif on_off=="on2":
            #GPIO.output(19, True)
            print("GPIO.output(19, True)")
        elif on_off=="off1":
            #GPIO.output(18, False)
            print("GPIO.output(18, False)")
        elif on_off=="off2":
            #GPIO.output(19, False)
            print("GPIO.output(19, False)")
        elif on_off=="back":
            break
        else:
            pass

#---------------------------MQTT FUNCTIONS------------------------------------- 

def heartbeat(r_topic):
    global death_note
    while True:
        for x in death_note:
            if x[1]==r_topic:
                kill=x[0]
        if kill==False:
            mqtt_client.publish(r_topic, "beat")
        else:
            break
        time.sleep(2)

def timeout_timer(id):
    #global timer_list, connections_count, clients_count
    global timer_list, clients_count
    tic=time.time()
    while True:
        found=False
        toc=time.time()
        if toc-tic>120:
            for x in clientslist:
                if x[0]==id:
                    print("\ntimeout di",id," premi invio\n")
                    mqtt_client.loop_stop()
                    mqtt_client.disconnect()
                    #connections_count-=1
                    clients_count-=1
            break
        for x in timer_list:
            if x[1]==id:
                found=True
                if x[0]==True:
                    tic=time.time()
                    x[0]=False
        if found==False:
            break


    #broker_host = "localhost"
    #broker_port = 1883
    #mqtt_client = mqtt.Client(servname, clean_session=True)
    #mqtt_client.connect(broker_host, broker_port)
    #mqtt_client.subscribe("topic1/#")
    #mqtt_client.on_message = on_message
    #mqtt_client.loop_start()


#------------------------------MAINCODE------------------------------------- 
#GPIO.setmode(GPIO.BCM)
#GPIO.setup(18, GPIO.OUT)
#GPIO.setup(19, GPIO.OUT)
#connections_count, clients_count, password, servname=inizio()
conn_state, clients_count, password, servname=inizio()
print("server id:",servname,"\nserver password:",password)
clientslist=[]
death_note=[]
timer_list=[]
while True:
    time.sleep(1)
    print("\nclients connessi:",clients_count,"/2")
    #print("1 = terminale\n2 = remoto(",connections_count,"/2 connesioni aperte)\n3 = esci\n4 = chiudi connessioni")
    print("1 = terminale\n2 = remoto(connessione",conn_state,"\n3 = esci\n4 = chiudi connessioni")
    start=input("")
    if start=="1":
        terminal()
    elif start=="2":
        #if connections_count<2:
        #    connections_count+=1

        def on_message(client, userdata, message):
            global death_note, timer_list
            global clients_count, connections_count
            print("ricevuto",message.payload.decode())
            raw_mess=message.payload.decode().split(".")
            mess=raw_mess[0]
            id_client=raw_mess[1]
            rensp_topic="rensp/"+id_client
            comm_topic="comm/"+id_client
            if mess==password:
                client.publish(rensp_topic, "ok")
                client.subscribe(comm_topic)
                death_note.append([False, rensp_topic])
                timer_list.append([True, id_client])
                threading.Thread(target=heartbeat, daemon=True, args=(rensp_topic,)).start()
                threading.Thread(target=timeout_timer, daemon=True, args=(id_client,)).start()
                client_data=(id_client, comm_topic)
                clientslist.append(client_data)
                clients_count+=1
            elif mess=="1":
                print("on")
                for x in timer_list:
                    if x[1]==id_client:
                        x[0]=True
            elif mess=="2":
                print("off")
                for x in timer_list:
                    if x[1]==id_client:
                        x[0]=True
                time.sleep(1)
            elif mess=="3":
                client.unsubscribe(comm_topic, rensp_topic) 
                clients_count-=1
                #connections_count-=1
                #if connections_count==0:
                #    print("client disconnesso")
                #    client.disconnect()
                if conn_state=="chiuso":
                    print("client disconnesso")
                    client.disconnect()
                for x in death_note:
                    if x[1]==rensp_topic:
                        x[0]=True
                        time.sleep(2)
                        index = death_note.index(x)
                        death_note.pop(index)
                for x in clientslist:
                    if x[0]==id_client:
                        index = clientslist.index(x)
                        clientslist.pop(index)
                for x in timer_list:
                    if x[1]==id_client:
                        index = timer_list.index(x)
                        timer_list.pop(index)
                print(id_client,"disconnesso")
                print("\npremi invio")
            else:
                client.publish(rensp_topic, "ko")
                for x in timer_list:
                    if x[1]==id_client:
                        x[0]=True
        if conn_state=="chiusa)":
            conn_state="aperta)"
            broker_host = "localhost"
            broker_port = 1883
            mqtt_client = mqtt.Client(servname, clean_session=True)
            mqtt_client.connect(broker_host, broker_port)
            #print("server client connesso")
            mqtt_client.subscribe("topic1/#")
            mqtt_client.on_message = on_message
            mqtt_client.loop_start()
        
    elif start=="3":
        print("bye bye")
        break
    elif start=="4":
        while True:
            print("\nclients connessi:",clients_count,"\n(connessione",conn_state)
            if conn_state=="aperta)" and clients_count==0:
                shut=input("chiudere connessione?(y/n)")
                if shut=="y":
                    conn_state="chiusa)"
                    mqtt_client.disconnect()
                    break
                elif shut=="n":
                    break
                else:
                    continue
            elif conn_state=="aperta)" and clients_count==1:
                client=clientslist[0]
                print("interrompere comunicazione con",client[0],"?(y/n)")
                kick=input()
                if kick=="y":
                    clients_count-=1
                    clientslist.pop(0)
                    if client[1].split("/")[0]=="comm":
                        mqtt_client.unsubscribe(client[1])
                        rtopic_clone="rensp/"+client[0]
                        for x in death_note:
                            if x[1]==rtopic_clone:
                                x[0]=True
                                time.sleep(2)
                                index = death_note.index(x)
                                death_note.pop(index)
                                break
                    else:
                        #gestire espulsione socket
                        pass
                elif kick=="n":
                    break
                else:
                    continue
            elif conn_state=="aperta)" and clients_count==2: 
                client1=clientslist[0]
                client2=clientslist[1]
                print("1 = espelli",client1,"\n2 = espelli",client2,"\n3 = annulla")
                kick=input()
                if kick=="1":
                    clientslist.pop(0)
                    if client1[1].split("/")[0]=="comm":
                        clients_count-=1
                        mqtt_client.unsubscribe(client1[1]) 
                        rtopic_clone="rensp/"+client1[0]
                        for x in death_note:
                            if x[1]==rtopic_clone:
                                x[0]=True
                                time.sleep(2)
                                index = death_note.index(x)
                                death_note.pop(index)
                    else:
                        #gestire espulsione socket
                        pass
                elif kick=="2":
                    clientslist.pop(1)
                    if client1[1].split("/")[0]=="comm":
                        clients_count-=1
                        mqtt_client.unsubscribe(client2[1]) 
                        rtopic_clone="rensp/"+client2[0]
                        for x in death_note:
                            if x[1]==rtopic_clone:
                                x[0]=True
                                time.sleep(2)
                                index = death_note.index(x)
                                death_note.pop(index)
                    else:
                        #gestire espulsione socket
                        pass
                elif kick=="3":
                    break
                else:
                    continue
            else:
                time.sleep(1.5)
                break

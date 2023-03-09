#import RPi.GPIO as GPIO
import threading, socket, pickle, time
import paho.mqtt.client as mqtt

#----------------------MAINCODE FUNCTIONS-----------------------------------            

def inizio():
    pner=0
    conn_count=0
    act_count=0
    op=False
    while True:
        passw=input("inserisci password di questo server: ")
        if passw=="":
            print("\nimposta una password prima di iniziare\n")
            continue
        else:
            break
    return pner, conn_count, act_count, op, passw

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
            print("\ndato inserito non valido\n")

#----------------------SOCKET FUNCTIONS-----------------------------------   

def socketsetup():
    host='localhost'                         
    port=5902
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    print("socket creato(host:",host," porta:",port,")")
    s.listen(2)
    return s

def ricezione(cs):
    global contr 
    try:
        contr=(cs.recv(1024).decode('utf-8'))
    except ConnectionAbortedError:
        print("connabort")
    except OSError:
        print("errore")

def ricezione_(cs, ca):
    global usr_confirm
    global usr
    global connections_count
    try: 
        data = cs.recv(1024)
        auth = pickle.loads(data)
        usr_confirm=auth[0]
        usr=auth[1]
        clientlist.append((cs, ca, usr))
    except ConnectionAbortedError:
        print("connabort_")
        cs.close()


def controlloremoto(cs, a, u):
    #cs.settimeout(10)
    global connections_count
    global clients_count
    global pinner
    global contr
    pinner+=1
    #global hello
    #threading.Thread(target=filenocheck, daemon=True, args=(cs,)).start()
    if pinner==1:
        pin=18
    if pinner==2:
        pin=19
    try:
        while True:
            #if cs.fileno() == -1:
                #print("client disconnesso")
            #if hello==False:
                #   print("client disconnesso")
                #  break
            if pin==19 and pinner==1:
                pin=18
            contr=""
            timerec=False
            threading.Thread(target=ricezione, args=(cs,)).start()
            tic=time.time()
            while True:
                toc=time.time()
                if contr=="" and toc-tic>60:
                    timerec=True
                    break
                elif contr!="":
                    break
            i=0
            safe=False
            if timerec==True:
                while i < len(clientlist):
                    if a in clientlist[i]:
                        print("\nTimeout: comunicazione con ",u,"terminata")
                        cs.close()
                        clients_count-=1
                        connections_count-=1
                        pinner-=1
                        safe=True
                        break
                    else:
                        i += 1
                if safe==True:
                    break
            if contr:
                if contr=="on":
                    #GPIO.output(pin, True)
                    print("                   ",u,"comando on su led ",pin)
                    pass
                elif contr=="off":
                    #GPIO.output(pin, False)
                    print("                   ",u,"comando off su led ",pin)
                    pass
                elif contr=="back":
                    print("                   comunicazione con ",u,a,"terminata\n")
                    cs.close()
                    connections_count-=1
                    clients_count-=1
                    pinner-=1
                    i = 0
                    while i < len(clientlist):
                        if a in clientlist[i]:
                            clientlist.pop(i)
                        else:
                            i += 1
                    break
    except Exception as e:
        print("                   errore nella comunicazione con ",u,a,":", e)
        cs.close()
        connections_count-=1
        pinner-=1
    except TimeoutError:
        print("client disconnesso per inattività")
        cs.close()
        connections_count-=1
        pinner-=1

def sockeThread(s_s):
    global password
    global connections_count
    global clients_count
    global usr_confirm
    global usr
    try:
        communication_socket, client_address = s_s.accept()
        print("                   connesso via socket attraverso ngrok con",client_address)
        print("...autenticazione in corso...")
        communication_socket.send(password.encode('utf-8'))
        #
        usr_confirm="vuoto"
        threading.Thread(target=ricezione_, args=(communication_socket, client_address)).start()
        tic=time.time()
        while True:
            time.sleep(0.5)
            toc=time.time()
            if usr_confirm=="vuoto" and toc-tic>40:
                break   
            elif usr_confirm=="autenticazione fallita":
                break   
            elif usr_confirm=="                    connesso":
                break
        if usr_confirm!="                    connesso":
            print("autenticazione fallita\n")
            communication_socket.close()
            connections_count-=1
            print("1 = terminale\n2 = remoto(",connections_count,"/2 connesioni aperte)\n3 = esci\n")
            return
        print(usr_confirm,"con",usr,client_address)
        clients_count+=1
        controlloremoto(communication_socket, client_address, usr)
    except:
        pass
    #print("SOCKclients connessi:",actual_count,"/2")
    #print("SOCK1 = terminale\n2 = remoto(",connections_count,"/2 connesioni aperte)\n3 = esci\n")

#-------------------------MQTT FUNCTIONS----------------------------------- 

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

def filenocheck(client_socket):
    global connections_count
    global hello
    hello=True
    while True:
        print(client_socket.fileno())
        time.sleep(1)

def mqttOperations(client):
    def on_message(client, userdata, message):
        global connections_count
        global message_received
        topic = message.topic
        print("ricevuto")
        payload = message.payload.decode("utf-8")
        if topic == "led/aut/rensp":
            if payload == "ko":
                print("\nPassword errata\n")
                connections_count -= 1
                return
            else:
                print(f"Password corretta. Ricevuto topic specifico: {payload}")
                client.subscribe(payload)
        else:
            print(f"Comando {payload} ricevuto su topic {topic}")
        message_received=True
    client.subscribe("led/aut/rensp")
    client.on_message = on_message
    client.loop_forever()
    #client.loop_start()

    message_received=False
    while not message_received:
            time.sleep(0.5)
            pass
    #client.loop_stop()

def passwordSpam(client):
    while True:
        client.publish("led/aut/spam", password, qos=2)
        #print("pubblicato")
        time.sleep(2)

#-----------------------DISCONNECTION FUNCTIONS----------------------------

def disconnections():
    global connections_count
    esci=False
    while True:
        simpleclose=input("1 = chiudi 1 connessione\n2 = chiudi tutte le connessioni\n3 = annulla\n")
        if simpleclose=="1":
            connections_count-=1
            print("1 connessione chiusa")
            esci=True
            break
        elif simpleclose=="2":
            connections_count=0
            print("connessioni chiuse")
            esci=True
            break
        elif simpleclose=="3":
            break
        else:
            print("\ndato inserito non valido\n")
    return esci

def dummykickout(dummy):
    global clients_count
    global connections_count
    try:
        dummy.close()
    except:
        print("chiusura socket non riuscita")
    try:
        dummy.disconnect()
    except:
        print("chiusura mqtt non riuscita")
    clients_count-=1
    connections_count-=1

def actvdisconnections():
    global clients_count
    global connections_count
    global clientlist
    global pinner
    esci=False
    i=0
    while True:
        if len(clientlist)>1:
            print("chi vuoi disconnettere?")
            for x in clientlist:
                i+=1
                print(i,"=",x[1],x[2])
            kickchoice=input("3 = annulla")
            if kickchoice=="1":
                dummykickout(clientlist[0][0])
                clientlist.pop(0)
                pinner-=1
                esci=True
                break
            elif kickchoice=="2":
                dummykickout(clientlist[1][0])
                clientlist.pop(1)
                pinner-=1
                esci=True
                break
            elif kickchoice=="3":
                break
            else:
                print("dato inserito non valido")
                continue
        else:
            print("disconnettere",clientlist[0][2],clientlist[0][1],"?")
            kickout=input("(y/n)")
            if kickout=="y":
                dummykickout(clientlist[0][0])
                clientlist.pop(0)
                pinner-=1
                esci=True
                break
            elif kickout=="n":
                break
            else:
                print("dato inserito non valido")
                continue
    return esci

#------------------------------MAINCODE------------------------------------- 
#GPIO.setmode(GPIO.BCM)
#GPIO.setup(18, GPIO.OUT)
#GPIO.setup(19, GPIO.OUT)
pinner, connections_count, clients_count, open, password=inizio()
global clientlist
clientlist=[]
while True:
    print("\nclients connessi:",clients_count,"/2")
    print("1 = terminale\n2 = remoto(",connections_count,"/2 connesioni aperte)\n3 = esci\n4 = chiudi connessioni")
    start=input("")
    if start=="1":
        terminal()
    elif start=="2":
        try:
            if connections_count==0:
                try:
                    server_socket.close()
                    client.disconnect()
                    open=False
                except NameError:
                    pass
            if connections_count==0 and open==False:
                server_socket=socketsetup()
                client=mqttsetup()
                time.sleep(1)
                open=True
            if connections_count>=2:
                print("\nlimite connessioni raggiunto!\n")
                continue
            connections_count+=1
            print("\n...apertura nuova connessione...\n")
            threading.Thread(target=sockeThread, daemon=True, args=(server_socket,)).start()
            threading.Thread(target=passwordSpam, daemon=True, args=(client,)).start()
            threading.Thread(target=mqttOperations, daemon=True, args=(client,)).start()
        except ConnectionAbortedError as e:
            print("ConnectionAbortedError: [WinError 10053] Connessione interrotta dal software del computer host")
            server_socket.close()
            connections_count-=1
            open=False
            continue
    elif start=="3":
        try:
            server_socket.close()
            client.disconnect()
            break
        except:
            break
    elif start=="4":
        if connections_count==0:
            print("\nnessuna connessione da chiudere\n")
            continue
        if clients_count==0 and connections_count>0:
            if disconnections()==False:
                continue
        else:
            while True:
                print("seleziona operazione:")
                actvdisc=input("1 = disconnetti clients\n2 = chiudi connessioni aperte\n3 = indietro\n")
                if actvdisc=="1":
                    print(clients_count,"clients connessi")
                    if actvdisconnections()==False:
                        continue
                    else:
                        break
                elif actvdisc=="2":
                    connections_count-=1
                    print("\nconnessione chiusa\n")
                    break
                elif actvdisc=="3":
                    break
                else:
                    print("\ndato non valido\n")
            #elif 
            
            #if connections_count==actual_count:
             #   pass
            #else:
             #   complexdisc=input("1 = ")

#---------------------------------------------------------------------------------------------------------------------

#implementare mqtt

#quando disconnetto da server qualche socket rimane collegato e se dopo mi ricollego ricevo una volta in più il messaggio

import funzioniS
import threading
import time
import pickle

def inizio():
    pinner=0
    connections_count=0
    open=False
    while True:
        password=input("inserisci password di questo server: ")
        if password=="":
            print("\nimposta una password prima di iniziare\n")
            continue
        else:
            break
    return pinner, connections_count, open, password

def filenocheck(client_socket):
    global connections_count
    global hello
    hello=True
    while True:
        print(client_socket.fileno())
        time.sleep(1)

def ricezione(cs):
    global contr 
    try:
        contr=(cs.recv(1024).decode('utf-8'))
    except ConnectionAbortedError:
        pass

def ricezione_(cs):
    global addr
    global usr 
    data = cs.recv(1024)
    auth = pickle.loads(data)
    addr=auth[0]
    usr=auth[1]


def controlloremoto(cs, a, u):
    #cs.settimeout(10)
    global connections_count
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
            if timerec==True:
                print("Timeout: comunicazione con ",u,"terminata")
                cs.close()
                connections_count-=1
                pinner-=1
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
                    print("                   comunicazione con ",u,a,"terminata")
                    cs.close()
                    connections_count-=1
                    pinner-=1
                    break
    except Exception as e:
        print("                   errore nella comunicazione con ",u,a,":", e)
        cs.close()
        connections_count-=1
        pinner-=1
    #except TimeoutError:
     #   print("client disconnesso per inattività")
      #  cs.close()
       # connections_count-=1
        #pinner-=1


def sockeThread(s_s):
    global password
    global connections_count
    global addr
    global usr
    communication_socket, client_address = s_s.accept()
    print("                   connesso via socket attraverso ngrok con",client_address)
    print("...autenticazione in corso...")
    communication_socket.send(password.encode('utf-8'))
    #
    addr="vuoto"
    threading.Thread(target=ricezione_, args=(communication_socket,)).start()
    tic=time.time()
    while True:
        time.sleep(0.5)
        toc=time.time()
        if addr=="vuoto" and toc-tic>60:
            break   
        elif addr=="autenticazione fallita":
            break   
        elif addr=="                    connesso":
            break
    if addr!="                    connesso":
        print("autenticazione fallita")
        communication_socket.close()
        connections_count-=1
        print("1 = terminale\n2 = remoto(",connections_count,"/2 connesioni aperte)\n3 = esci\n")
        return
    print(addr,"con",usr,client_address)
    controlloremoto(communication_socket, client_address, usr)
    print("1 = terminale\n2 = remoto(",connections_count,"/2 connesioni aperte)\n3 = esci\n")

def mqttOperations(client):
    def on_message(client, userdata, message):
        global connections_count
        topic = message.topic
        payload = message.payload.decode("utf-8")
        print("ricevuto")
        #server riceve messaggio su led/aut/rensp
        if topic == "led/aut/rensp":
            #se messaggio "ko" server connections_count-1 e ricomincia ciclo
            if payload == "ko":
                print("\nPassword errata\n")
                connections_count -= 1
                return
            else:
                #se messaggio topic(led/usr) server si sottoscrive al canale e fa corrispondere on/off/back
                print(f"Password corretta. Ricevuto topic specifico: {payload}")
                client.subscribe(payload)
        else:
            print(f"Comando {payload} ricevuto su topic {topic}")
            # gestisci il comando (on/off/back) in base al topic
    #server si sottoscrive a canale led/aut/rensp
    client.subscribe("led/aut/rensp")
    client.on_message = on_message
    client.loop_forever()

def passwordSpam(client):
    while True:
    #server pubblica password a ripetizione su topic led/aut/spam a cui client è già connesso (no retain)
        client.publish("led/aut/spam", password, qos=2)
        time.sleep(2)


pinner, connections_count, open, password=inizio()
client=""
while True:
    print("1 = terminale\n2 = remoto(",connections_count,"/2 connesioni aperte)\n3 = esci\n")
    start=input("")
    if start=="1":
        funzioniS.terminal()
    elif start=="2":
        try:
            if connections_count==0 and open==False:
                server_socket, mqtt_client=funzioniS.setup() 
                if not client:
                    client=funzioniS.mqttsetup()
                open=True
                time.sleep(2)
            if connections_count>=2:
                print("\nlimite connessioni raggiunto!\n")
                continue
            connections_count+=1
            print("\n...in ascolto...\n")
            threading.Thread(target=sockeThread, daemon=True, args=(server_socket,)).start()
            threading.Thread(target=passwordSpam, daemon=True, args=(client,)).start()
            threading.Thread(target=mqttOperations, daemon=True, args=(client,)).start()
            #client riceve password da led/aut/spam e fa verifica
            #se verifica è corretta client pubblica su topic led/aut/rensp il topic client specifico (led/usr)
            #se verifica è scorretta client pubblica su topic led/aut/rensp "ko"
        except ConnectionAbortedError as e:
            print("ConnectionAbortedError: [WinError 10053] Connessione interrotta dal software del computer host")
            server_socket.close()
            connections_count-=1
            open=False
            continue
    elif start=="3":
        try:
            server_socket.close()
            break
        except:
            break

#rivedere connessione mqtt (si connette anche a connessione chiusa)
#aggiungi funzionalità per chiudere connessione con un solo client a scelta
#rimandare al codice base il server socket o topic corrispondente a client 1/2
#creare variabile globale lista per aggiungere ogni topic/connection socket per poi poterli eliminare

#controllare auth0 line 37
#aggiungere usr
#implementare il tutto su client
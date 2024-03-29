#------------------------------------------------------------------------
#///////////////////////////////////////////////////////////////////////
#-------------------------LIBRERIRES----------------------------------- 
#import RPi.GPIO as GPIO
import threading, socket, time, random, getpass
import paho.mqtt.client as mqtt
#------------------------------------------------------------------------
#///////////////////////////////////////////////////////////////////////
#-------------------------FUNCTIONS------------------------------------ 
#-------------------------operators-----------------------------------            
def inizio():#imposta lo stato della connessione, crea id del server e fa inserire password
    conn_state="chiusa)"
    name="Server"+str(random.randint(1,999))
    while True:
        passw=getpass.getpass("inserisci password di questo server: ")
        if passw=="":
            print("\nimposta una password prima di iniziare\n")
            continue
        else:
            break
    return conn_state, passw, name

def timeout_timer(id):#timer di 40 secondi. controlla lo stato di attività di ogni client. al timeout espelle il client
    tic=time.time()#inizia a contare
    while True:
        found=False
        toc=time.time()#tiene il conto dopo ogni giro
        if toc-tic>40:#confrontando i due conteggi, se sono passati + di 40 sec
            for x in clientslist:
                if x[0]==id:
                    print("\ntimeout di",id," premi invio\n")
                    clientslist.pop(clientslist.index(x))
                    kick_out(id)
            break
        for x in timer_list:
            if x[0]==id:
                found=True#continua il giro solo se il client è ancora timerlist
                if x[1]==True:
                    tic=time.time()#reimposta tic se timerlist==True (operazione eseguita da client) e lo risetta a false
                    x[1]=False
        if found==False:
            break#client non presente nella timerlist
        time.sleep(1)

def restore_time(id):#segnala attività del client facendo resettare il suo timer
    for x in timer_list:
        if x[0]==id:#imposta elemento di client in timerlist a true per riavviare timer
            x[1]=True

def clean_list(elementi, superlista):#elimina un client da una o più liste
    for lista in superlista:#scorre ogni lista inserita

        if lista==queue_list:#toglie elemento dalla coda
            lista.pop(lista.index(elementi[0]))

        elif lista==death_note:#mette True da passare come "kill" a death_note, apetta 2 secondi per assicurarsi che funzione heartbeat abbia finito e poi toglie client
            for x in lista:
                if x[1]==elementi[1]:
                    x[0]=True
                    time.sleep(2)
                    lista.pop(lista.index(x))
        else:
            for x in lista:#le altre liste con id del client come primo elemento  (da eliminare)
                if x[0]==elementi[0]:
                    lista.pop(lista.index(x))

def kick_out(client):#espelle un client e lo elimina dalle liste
    try:
        client[1].close()
    except:#se non è un socket desottoscrive da topic mqtt corrispondente a client e ripulisce le liste
        mqtt_client.unsubscribe(client[1])
        rtopic_clone="rensp/"+client[0]
        clean_list([0,rtopic_clone],[death_note])
    clean_list([client[0]],[timer_list,clientslist,queue_list])

def pin_assign(id):#assegna pin (18 o 19) al client
    for x in clientslist:
        if x[0]==id:#assegna sempre 18 al primo client della lista e 19 al secondo
            pin=clientslist.index(x)
    if pin==0:
        pin=18
    else:
        pin=19
    return pin
#--------------------------terminal------------------------------------- 
def terminal():#permette di eseguire comandi sul led da terminale
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
#----------------------------mqtt---------------------------------------
def heartbeat(r_topic):#manda segnali di attività periodici al client
    while True:
        for x in death_note:#ogni 2 secondi controlla lo stato di "kill" assegnato ad ogni client attivo; se è False manda un "beat", altrimenti esce
            if x[1]==r_topic:
                kill=x[0]
        if not kill:
            mqtt_client.publish(r_topic, "beat")
        else:
            break
        time.sleep(2)
#---------------------------socket---------------------------------------
def socket_comm(communication_socket, id):#ricezione messaggi dal client autenticato tramite socket
    while conn_state=="aperta)":
        #______decodificazione_messaggio______
        raw_mess=communication_socket.recv(1024).decode('utf-8').split(".")
        mess=raw_mess[0]
        id=raw_mess[1]
        #______gestione_messaggi______________
        restore_time(id)#resetta timer del client
        if mess=="1":
            pin=pin_assign(id)
            print("on da",id,"sul pin",pin)
            #GPIO.output(pin, True)
        elif mess=="2":
            pin=pin_assign(id)
            print("off da",id,"sul pin",pin)
            #GPIO.output(pin, False)
        elif mess=="3":#disconnessione e rimozione da lista del client
            for x in clientslist:
                if x[0]==id:
                    kick_out(x)
            print(id,"disconnesso")
            break

def clients_waiter():#thread che accetta connessioni in arrivo, crea socket ed incanala client in thread handle_socket_client
    try:
        communication_socket, client_address = s.accept()
        threading.Thread(target=handle_socket_client,daemon=True,args=(communication_socket,)).start()
    except OSError as e:
        print(e)

def handle_socket_client(communication_socket):#richiama thread clients_waiter quando c'è spazio; a connessione aperta riceve messaggi e gestisce autenticazioni

    if len(clientslist)<2:#richiama clients_waiter per accettare altre connessioni se i client connessi sono meno di 2
        threading.Thread(target=clients_waiter,daemon=True,args=()).start()

    while conn_state=="aperta)":#a connessione aperta
        try:
            #______decodificazione_messaggio____________________
            raw_mess=communication_socket.recv(1024).decode('utf-8').split(".")
            mess=raw_mess[0]
            id=raw_mess[1]
            #______controllo_della_coda__________________________
            if mess not in ["1","2","3"] and len(queue_list)<2:#aggiunge a lista coda (queue_list) se client non ci è già presente
                if not queue_list or queue_list[0]!=id:
                    queue_list.append(id)
            #______gestione_messaggi_autenticazione
            if id in queue_list:#gestione messaggio di autenticazione una volta che il client è in lista
                if mess==password:#password ricevuta giusta
                    print(mess,id,"ok")
                    communication_socket.send("ok".encode('utf-8'))#invia segnale per iniziare a comunicare
                    clientslist.append([id,communication_socket])#aggiunge il client a lista clients
                    timer_list.append([id, True])#inizializza e starta il timer per il client autenticato
                    threading.Thread(target=timeout_timer, daemon=True, args=(id,)).start()
                    socket_comm(communication_socket,id)#inizia funzione per recezione comandi da client
                elif mess=="bye":#messaggio del client che si è disconnesso
                    clean_list([id],[queue_list])
                    communication_socket.close()#tolgo dalla lista e chiudo socket
                else:#password ricevuta sbagliata
                    communication_socket.send("ko".encode('utf-8'))#invia segnale di errore
                    restore_time(id)#resetta timer del client
                    print(mess, id,"ko") 

            else:#la coda è piena 
                communication_socket.send("no".encode('utf-8'))#invia segnale di coda piena
                print(mess, id,"no")
                communication_socket.close()#chiude socket e pulisce liste                                    ///////////
                clean_list([id],[clientslist,timer_list,queue_list])   

        #_______disconnection___________
        except (OSError,IndexError):#in caso di disconnessione
            pass
#------------------------------------------------------------------------
#///////////////////////////////////////////////////////////////////////
#---------------------------MAINCODE------------------------------------- 
#GPIO.setmode(GPIO.BCM)
#GPIO.setup(18, GPIO.OUT)
#GPIO.setup(19, GPIO.OUT)
clientslist, death_note, timer_list, queue_list=[],[],[],[]
conn_state, password, servname=inizio()
print("server id:",servname,"\nserver password:",password)
while True:
    time.sleep(1)
    print("\nclients connessi:",len(clientslist),"/2")
    print("1 = terminale\n2 = remoto(connessione",conn_state,"\n3 = esci\n4 = chiudi connessioni")
    start=input("")

    if start=="1":#operazioni da terminale
        terminal()

    elif start=="2":#operazioni da remoto

        def on_message(client, userdata, message):
            #______decodificazione_messaggio____________________
            mess=message.payload.decode('utf-8').split(".")[0]
            id_client=message.payload.decode('utf-8').split(".")[1]
            rensp_topic="rensp/"+id_client
            comm_topic="comm/"+id_client

            #________ricezione_comandi__________________________
            if mess=="1":#assegno pin, gestisco output e resetto timer relativo a client
                pin=pin_assign(id_client)
                #GPIO.output(pin, True)
                print("on da",id_client,"sul pin",pin)
                restore_time(id_client)
            elif mess=="2":#assegno pin, gestisco output e resetto timer relativo a client
                pin=pin_assign(id_client)
                #GPIO.output(pin, False)
                print("off da",id_client,"sul pin",pin)
                restore_time(id_client)
            elif mess=="3":#espulsione client
                pin=pin_assign(id_client)
                print("back da",id_client,"sul pin",pin)
                for x in clientslist:
                    if x[0]==id_client:
                        kick_out(x)#passo elemento relativo a client contenente il socket per espellerlo
                print(id_client,"disconnesso")
                print("\npremi invio")

            #_______gestione_login_______________________________
            elif len(queue_list)<2:#verifica numero di client accodati
                if not queue_list or queue_list[0]!=id_client:#aggiunge id_client a queue_list(coda) se non è ancora presente
                    queue_list.append(id_client)
                if mess==password:#password inserita dall'utente corretta
                    clientslist.append([id_client,comm_topic])#implemento liste
                    death_note.append([False, rensp_topic])
                    timer_list.append([id_client, True])
                    client.publish(rensp_topic, "ok")#pubblico ok e sottoscrivo a topic per ricevere messaggi da client
                    client.subscribe(comm_topic)
                    threading.Thread(target=heartbeat, daemon=True, args=(rensp_topic,)).start()#inizio thread per segnalare recezione stabile a client
                    threading.Thread(target=timeout_timer, daemon=True, args=(id_client,)).start()#faccio partire il timer relativo al client appena loggato
                else:#password errata
                    client.publish(rensp_topic, "ko")
                    restore_time(id_client)#resetto timer
            else:#la coda è già piena 
                client.publish("no")#pubblico no e tolgo client dalle liste
                clean_list([id_client],[clientslist,timer_list,queue_list])

        while True:
        #_______local/other____________
            rem_type=input("su che rete preferisci comunicare?\n1 = rete locale\n2 = altre reti")
            if rem_type=="1":
                mqtt_host="localhost"
                break
            elif rem_type=="2":
                mqtt_host="192.168.1.100"
                break


        if conn_state=="chiusa)":#1: se conn_state è "chiusa)" inizializza mqtt e socket e setta conn_state ad "aperta)"
        #_______mqtt_init____________
            conn_state="aperta)"
            broker_port = 1883
            mqtt_client = mqtt.Client(servname, clean_session=True)
            mqtt_client.connect(mqtt_host, broker_port)
            mqtt_client.subscribe("topic1/#")
            mqtt_client.on_message = on_message#al ricevimento di messaggi esegue on_message
            mqtt_client.loop_start()

        #_______socket_init____________                 
            socket_port=5902
            socket_host="localhost"
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((socket_host,socket_port))
            s.listen(0)
            threading.Thread(target=clients_waiter,daemon=True,args=()).start()#starta thread clients_waiter per accettare client e gestirli
        
    elif start=="3":#chiusura programma
        print("bye bye")
        break#esce dal ciclo 

    elif start=="4":#gestione/chiusura connessioni
        while True:
            print("\nclients connessi:",len(clientslist),"\n(connessione",conn_state)#visualizza stato connessione
            if conn_state=="aperta)":

                #_________no_clients_______
                if len(clientslist)==0:#conn_state aperta), nessun client connesso
                    shut=input("chiudere connessione?(y/n)")
                    if shut=="y":#conn_state->chiusa), disconnessione broker e socket
                        conn_state="chiusa)"
                        mqtt_client.disconnect()
                        s.close()
                        break
                    elif shut=="n":#torna indietro
                        break

                #__________1_client_________
                elif len(clientslist)==1:#conn_state aperta), 1 client connesso
                    client=clientslist[0]#imposta client all'unico id contenuto in clientslist
                    print("interrompere comunicazione con",client[0],"?(y/n)")
                    kick=input()
                    if kick=="y":#disconnessione client e cancellazione dalle liste
                        kick_out(client)
                    elif kick=="n":#torna indietro
                        break
                
                #__________2_client_________
                elif len(clientslist)==2:#conn_state aperta), 2 client connessi
                    client1=clientslist[0]#imposta client1 al primo id contenuto in clientslist
                    client2=clientslist[1]#imposta client2 al secondo id contenuto in clientslist
                    print("1 = espelli",client1[0],"\n2 = espelli",client2[0],"\n3 = annulla")
                    kick=input()
                    if kick=="1":#disconnessione client1 e cancellazione dalle liste
                        kick_out(client1)
                    elif kick=="2":#disconnessione client2 e cancellazione dalle liste
                        kick_out(client2)
                    elif kick=="3":#torna indietro
                        break
            else:
                time.sleep(1.5)
                break

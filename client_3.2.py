import random, socket, threading, time, getpass
import paho.mqtt.client as mqtt

#-----------------------MAINCODE FUNCTIONS-----------------------------------   

def inizio():#creazione username unico
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

def topics_setup(id):#creazione topics personalizzati
    rensp="rensp/"+id
    tp1="topic1/"+id
    return rensp, tp1

#-------------------------MQTT FUNCTIONS-------------------------------------

def timeout_timer():#timer per disconnettere in seguito ad inattività
    global start_main_loop, tic, timerblock, pause, stop_spam
    while True:
        tic=time.time()#inizia a contare
        while not timerblock:#finchè non viene settato timerblock True 
            toc=time.time()
            if toc-tic>120:#confronta tempi: dopo 120 secondi di inattività disconnette, blocca loops in esecuzione e riinizia il principale
                print("\ntimeout. premi invio\n")
                client.loop_stop()
                client.disconnect()
                start_main_loop=True
                timerblock=True
                stop_spam=True
                if T_comandi.is_alive():#arresta il thread per i comandi se sta eseguendo
                    pause=True
                break

def heartbeat():#verifica costante di connessione col server, se non riceve segnali per 10 secondi si disconnette
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

def comandi_mqtt():#gestione invio di segnali dopo atenticazione
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

def spam(t,p):#spam password in attesa di segnali di ricezione
    global start_main_loop, timerblock
    timeout=0
    time.sleep(2)
    while not stop_spam:
        if timeout<5:#attende client per 10 secondi
            client.publish(t,p)
            time.sleep(2)
            timeout+=1
        else:
            print("\ntimeout\n")
            start_main_loop=True
            timerblock=True
            client.loop_stop()
            client.disconnect()
            break

#------------------------SOCKET FUNCTIONS-------------------------------------

def comandi_socket():#gestione invio di segnali dopo atenticazione
    while True:
        on_off=input("1 = on\n2 = off\n3 = back\n")
        try:
            if on_off in ["1","2"]:
                #tic=time.time()
                on_off_mess=on_off+"."+username
                client_socket.send(on_off_mess.encode('utf-8'))
            elif on_off=="3":
                on_off_mess=on_off+"."+username
                client_socket.send(on_off_mess.encode('utf-8'))
                client_socket.close()
                break
            else:
                print("\ndato inserito non valido\n")
                #tic=time.time()
        except ConnectionResetError:
            print("\nserver disconnesso\n")
            break


#------------------------------MAINCODE--------------------------------------

#_______definizione_variabili/threads________________________
username=inizio()
rensptopic, topic1=topics_setup(username)
make="comm/"+username
sure="3."+username
start_main_loop=True#permette di eseguire il loop del maincode
T_timer=threading.Thread(target=timeout_timer, daemon=True)
timerblock=False#permette di eseguire il loop di timeout_timer
T_comandi=threading.Thread(target=comandi_mqtt, daemon=True)
pause=False#permette di eseguire il loop di comandi_mqtt e heartbeat
T_beat=threading.Thread(target=heartbeat, daemon=True)


while True:   
    if start_main_loop==True:#riinizia loop solo se comunicazione terminata
        #________definizione_variabili______________
        client_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        stop_spam=False#per permettere di spammare password
        connesso=None#indica a che stadio è il client: None=non connesso; False=connesso ma non autenticato; True=connesso e autenticato
        aut_count=2#per contare quante volte viene provata una password
        timeout=0#per gestire timeout in attesa del server

        mod=input("\n1 = connessione via ngrok/socket\n2 = connessione via mqtt\n3 = esci\n")

        #__________modalità_socket___________________
        if mod =="1":
            while True:
            #_______local/other____________
                rem_type=input("\nsu che rete preferisci comunicare?\n1 = rete locale\n2 = altre reti")
                if rem_type=="1":
                    print("\nrete locale selezionata\n")
                    break
                elif rem_type=="2":
                    print("\naltre reti selezionato\n")
                    break

            if rem_type=="2":
                while True:
                    host_n=input("inserisci indirizzo ngrok: ")
                    try:
                        port_n=int(input("inserisci porta ngrok: "))
                        break
                    except:
                        print("\nporta non valida\n")
            else:
                host_n="localhost"
                port_n=5902

            print("...in attesa del server, non premere pulsanti...")
            while connesso==None:

                #________connessione__________________________
                if timeout<10:#attende client per 10 secondi
                    try:
                        client_socket.connect((host_n,port_n))
                        start_main_loop=False
                        connesso=False
                    except Exception as e:
                        print(e)
                        timeout+=1
                        time.sleep(2)
                else:
                    connesso=False
            if timeout>=10:
                print("timeout")

            else:#a connessione riuscita
                #________autenticazione__________________________
                try:
                    pw=getpass.getpass("inserire password: ")+"."+username
                    client_socket.send(pw.encode('utf-8'))#invia password e riceve risposta
                    aut=client_socket.recv(1024).decode('utf-8')
                    if aut=="ok":
                        connesso==True
                        print("ok")
                        comandi_socket()#inizia a inviare comandi al server
                        start_main_loop=True
                    else:
                        for x in range(2):#prova altre 2 volte la password
                            print(x)
                            print("password errata.",aut_count,"tentativi rimasti")
                            pw=getpass.getpass("inserire password: ")+"."+username
                            client_socket.send(pw.encode('utf-8'))
                            aut=client_socket.recv(1024).decode('utf-8')
                            if aut=="ok":
                                connesso==True
                                print("ok")
                                comandi_socket()
                                start_main_loop=True
                                break #                                        
                            elif aut=="ko":
                                aut_count-=1
                            elif aut=="no":
                                print("\nserver pieno\n")
                                make_sure="bye."+username
                                client_socket.send(make_sure.encode('utf-8'))
                                client_socket.close()
                                start_main_loop=True
                            if not aut_count:#tentativi di autenticazione esauriti, invio messaggio chiusura e chiusura socket
                                print("\npassword errata. tentativi esauriti.\n")
                                make_sure="bye."+username
                                client_socket.send(make_sure.encode('utf-8'))
                                client_socket.close()
                                start_main_loop=True
                except ConnectionResetError or ConnectionAbortedError:#gestione disconnessione da server
                    print("\nserver disconnesso / Timeout\n")
                    start_main_loop=True
                    client_socket.close()
                        
        #__________modalità_mqtt___________________
        elif mod=="2":

            #__________connessione___________________
            def on_connect(client, userdata, flags, rc): #a connessione attende client e manda password (eventualmente a spam)
                global start_main_loop, tic, timerblock
                start_main_loop=False
                try:
                    T_timer.start()#inizializza thread timer; se gia inizializzara riabilita loop timer
                except:
                    timerblock=False
                pw=getpass.getpass("inserire password: ")+"."+username
                tic=time.time()
                client.publish(topic1,pw)
                print("...in attesa del server, non premere pulsanti...")
                threading.Thread(target=spam, args=(topic1,pw)).start()
                

            #__________ricezione___________________
            def on_message(client, userdata, message):
                global tic, aut_count, start_main_loop, alive, pause, timerblock, stop_spam
                stop_spam=True
                rensp=message.payload.decode('utf-8')
                if rensp=="ok":#password giusta
                    try:
                        T_comandi.start()#inizia thread per inviare comandi e per verificare connessinone con client
                        T_beat.start()
                    except:
                        pause=False
                    pass
                elif rensp=="ko":#password sbagliata
                    if not aut_count:#se limite superato, disconnessione e restart del main loop
                        print("\npassword errata. tentativi esauriti.\n")
                        client.publish(make,sure)
                        client.loop_stop()
                        client.disconnect()
                        timerblock=True
                        start_main_loop=True
                    else:
                        print("\npassword errata.",aut_count,"tentativi rimasti")#con ancora tentativi disponibili chiede di nuovo password
                        retry=getpass.getpass("password: ")+"."+username
                        tic=time.time()
                        client.publish(topic1,retry)
                        aut_count-=1
                elif rensp=="no":#coda del server piena, disconnessione
                    print("\nserver pieno\n")
                    client.publish(make,sure)
                    client.loop_stop()
                    client.disconnect()
                    timerblock=True
                    start_main_loop=True
                elif rensp=="beat":#ogni volta che viene ricevuto il "beat" del server si resetta il conteggio heartbeat
                    alive=time.time()

            #__________inizializzazione_mqtt.client___________________
            broker_host = "localhost"
            #brocker_host = mosquitto[...]
            broker_port = 1883
            client = mqtt.Client(username)
            client.connect(broker_host, broker_port)
            client.subscribe(rensptopic)
            client.on_connect = on_connect
            client.on_message = on_message
            client.loop_start()
            time.sleep(1)

        elif mod=="3":#esce dal programma
            break
        else:
            continue

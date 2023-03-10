import socket


def setupconnection():
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            p=int(input("inserire porta: "))
        except:
            print("\ndato inserito non valido\n")
            continue
        h=input("inserire url ngrok: ")
        break
    return s,h,p

def controlloremoto(cs):
    while True:
        try:
            contr=input("on = led on\noff = led off\nback = exit\n")
            if contr=="on":
                cs.send("on".encode('utf-8'))
            elif contr=="off":
                cs.send("off".encode('utf-8'))
            elif contr=="back":
                cs.send("back".encode('utf-8'))
                print("\ndisconnessione\n")
                cs.close()
                break
            else:
                print("\ninserisci un dato valido\n")
                continue
        except ConnectionAbortedError:
            print("[WinError 10053] Connessione interrotta dal software del computer host")
            break
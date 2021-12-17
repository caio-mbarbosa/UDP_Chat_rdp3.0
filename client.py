from socket import *
import sys
import os
import time
import threading

# Abrindo um socket UDP e setando o ip, porta e número de bytes do buffer
socket_client = socket(AF_INET, SOCK_DGRAM)
client_ip = gethostbyname(gethostname())
client_port = 4455
server_ip = client_ip # pois a troca de pacotes está acontecendo no mesmo IP
server_port = 6789
server_ip_port_tuple = (server_ip, server_port)


def rdt_send_message(ip_port_tuple):
    buffer_size = 1024
    state = 0

    bye = False
   
    # Enviando pacotes de 1024 em 1024 bytes para o servidor, até que o arquivo seja completamente enviado
    while True:
        if(state == 0): 
            currMsg = input()
            if currMsg == "bye":
                bye = True
            
            currMsg = b'0' + currMsg[:buffer_size-1].encode()


            if(socket_client.sendto(currMsg, ip_port_tuple)):
                receiver_pkt = None
                state = 1

        if(state == 1):
            try:
                socket_client.settimeout(0.2)
                receiver_pkt, _ = socket_client.recvfrom(buffer_size) 
                #print("RDT_SEND: pacote que eu recebi do servidor (state 1): " + receiver_pkt.decode())
            except timeout:
                #print("RDT_SEND: Precisei retransmitir! (state 1): " + str(currMsg))
                socket_client.sendto(currMsg, ip_port_tuple)
            
            if receiver_pkt is not None:
                if receiver_pkt[:1] == b'0': #b'0': status de sucesso
                    if bye: 
                        break
                    state = 2

        if(state == 2): 
            currMsg = input()
            if currMsg == "bye":
                bye = True
            
            currMsg = b'1' + currMsg[:buffer_size-1].encode()


            if(socket_client.sendto(currMsg, ip_port_tuple)):
                receiver_pkt = None
                state = 3

        if(state == 3):
            try:
                socket_client.settimeout(0.2)
                receiver_pkt, _ = socket_client.recvfrom(buffer_size) 
                #print("RDT_SEND: pacote que eu recebi do servidor (state 2): " + receiver_pkt.decode())
            except timeout:
                #print("RDT_SEND: Precisei retransmitir (state 2) " + str(currMsg))
                socket_client.sendto(currMsg, ip_port_tuple)
            
            if receiver_pkt is not None: 
                if receiver_pkt[:1] == b'1':
                    if bye: 
                        break
                    state = 0

def rdt_receive_message(state):
    buffer_size = 1024
    message = ""
    
    if(state == 0): 
        # Estado que estamos esperando receber um pacote com 1o byte do header == 0
        pkt, ip_port_tuple = socket_client.recvfrom(buffer_size)

        if(pkt[:1] == b'2'):
            #print("RDT_RECEIVE: eu recebi a mensagem que eu deveria receber mesmo! (com b=2)")
            #print("RDT_RECEIVE: mensagem: " + str(pkt[1:].decode()))
            message = pkt[1:].decode()    #f.write(pkt[1:])
            socket_client.sendto(b'2', ip_port_tuple)
            state = 1
            return message, ip_port_tuple, state
        elif(pkt[:1] == b'3'):
            #print("RDT_RECEIVE: eu recebi uma mensagem que NÃO deveria receber, e dei ACK (to no b=2, mas veio b=3)")
            socket_client.sendto(b'3', ip_port_tuple)
            return "", None, state
            

    if(state == 1):
        # Estado que estamos esperando receber um pacote com 1o byte do header == 1
        pkt, ip_port_tuple = socket_client.recvfrom(buffer_size)

        if(pkt[:1] == b'3'):
            #print("RDT_RECEIVE: eu recebi a mensagem que eu deveria receber mesmo! (com b=3)")
            #print("RDT_RECEIVE: mensagem: " + str(pkt[1:].decode()))
            message = pkt[1:].decode()      #f.write(pkt[1:]) # cara, esse write aq ta certo msm?
            socket_client.sendto(b'3', ip_port_tuple)
            state = 0 
            return message, ip_port_tuple, state
        elif(pkt[:1] == b'2'):
            #print("RDT_RECEIVE: eu recebi uma mensagem que NÃO deveria receber, e dei ACK (to no b=3, mas veio b=2)")
            socket_client.sendto(b'2', ip_port_tuple)
            return "", None, state

    return "", None, state


def SEND():
    rdt_send_message(server_ip_port_tuple)
    print("Você foi desconectado com sucesso da sala!")
    return

def RECEIVE():
    state = 0 
    while True:
        try:
            retorno, _ ,state = rdt_receive_message(state)
            if retorno != "":
                print(retorno)
        except timeout:
            print('', end='', sep='')
    

# client_name = input("Digite o seu nome: ")
# rdt_send_message(client_name, server_ip_port_tuple)

# Enviando o nome do arquivo para o servidor

# Using Multi-threading
send_thread = threading.Thread(target=SEND)
receive_thread = threading.Thread(target=RECEIVE)
send_thread.start()
receive_thread.start()
print("Obrigado por usar nosso chat!")
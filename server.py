from socket import *
import os
import datetime


# Abrindo um socket UDP e setando o ip, porta e númeero de bytes do buffer
server_ip = gethostbyname(gethostname())
server_port = 6789
server_socket = socket(AF_INET, SOCK_DGRAM)
server_socket.bind((server_ip, server_port))

dic_Nomes = {}


# FUNÇÕES

def rdt_send_message(message, ip_port_tuple):
    buffer_size = 1024
    state = 0
   
    # PRECISAMOS DECIDIR QUAL O 1o BYTE DE ACK QUE O SERVIDOR ESPERA

    state = dic_Nomes[ip_port_tuple][2]

    # Enviando pacotes de 1024 em 1024 bytes para o servidor, até que o arquivo seja completamente enviado
    currMsg = message.encode()

    while state == 0 or state == 1: 

        if(state == 0): 
            currMsg = b'2' + currMsg[:buffer_size-1]
            if(server_socket.sendto(currMsg, ip_port_tuple)):
                receiver_pkt = None
                state = 1

        if(state == 1):

            try:
                server_socket.settimeout(0.2)
                receiver_pkt, _ = server_socket.recvfrom(buffer_size) 
                #print("RDT_SEND: pacote que eu recebi do cliente (state 1): " + receiver_pkt.decode())
            except timeout:
                #print("RDT_SEND: Precisei retransmitir! (state 1): " + str(currMsg))
                server_socket.sendto(currMsg, ip_port_tuple)
            
            if receiver_pkt is not None:
                if receiver_pkt[:1] == b'2': #b'2': status de sucesso
                    #print("RDT_SEND: mandei pro cliente com b=2")
                    dic_Nomes[ip_port_tuple][2] = 2
                    return
    
    while state == 2 or state == 3:
       
        if(state == 2): 
            currMsg = b'3' + currMsg[:buffer_size-1]
            if(server_socket.sendto(currMsg, ip_port_tuple)):
                receiver_pkt = None
                state = 3

        if(state == 3):
            try:
                server_socket.settimeout(0.2)
                receiver_pkt, _ = server_socket.recvfrom(buffer_size) 
                #print("RDT_SEND: pacote que eu recebi do cliente (state 1): " + receiver_pkt.decode())
            except timeout:
                #print("RDT_SEND: Precisei retransmitir! (state 1): " + str(currMsg))

                server_socket.sendto(currMsg, ip_port_tuple)
            
            if receiver_pkt is not None: 
                if receiver_pkt[:1] == b'3':
                    #print("RDT_SEND: mandei pro cliente com b=3")
                    dic_Nomes[ip_port_tuple][2] = 0
                    return
                        


def rdt_receive_message():
    buffer_size = 1024
    message = ""


    # trecho do codigo que vamos usar nosso dicionario para DESCOBRIR qual o STATE de um cliente
    pkt, ip_port_tuple = server_socket.recvfrom(buffer_size)

    if ip_port_tuple not in dic_Nomes:
        message += pkt[1:].decode()    
        server_socket.sendto(b'0', ip_port_tuple)
        return message, ip_port_tuple
    
    state = dic_Nomes[ip_port_tuple][1]


    if(state == 0): 
       
        # Estado que estamos esperando receber um pacote com 1o byte do header == 0
        if(pkt[:1] == b'0'):
            #print("RDT_RECEIVE: eu recebi a mensagem que eu deveria receber mesmo! (com b=0)")
            #print("RDT_RECEIVE: mensagem: " + str(pkt[1:].decode()))
            message += pkt[1:].decode()    
            server_socket.sendto(b'0', ip_port_tuple)
            dic_Nomes[ip_port_tuple][1] = 1
            return message, ip_port_tuple

        elif(pkt[:1] == b'1'):
            server_socket.sendto(b'1', ip_port_tuple)
            return "", None
            

    if(state == 1):
       
        # Estado que estamos esperando receber um pacote com 1o byte do header == 1
        if(pkt[:1] == b'1'):
            #print("RDT_RECEIVE: eu recebi a mensagem que eu deveria receber mesmo! (com b=1)")
            #print("RDT_RECEIVE: mensagem: " + str(pkt[1:].decode()))
            message += pkt[1:].decode()      
            server_socket.sendto(b'1', ip_port_tuple)
            dic_Nomes[ip_port_tuple][1] = 0 
            return message, ip_port_tuple
        elif(pkt[:1] == b'0'):
            server_socket.sendto(b'0', ip_port_tuple)
            return "", None

    return "", None
    

def add_user_to_list(nome, ip_port_tuple):
    dic_Nomes[ip_port_tuple] = [nome,1,0] 
    return


def send_user_list(ip_port_tuple):
    messageCurr = ""
    for users in dic_Nomes:
        messageCurr += "Nome: " + dic_Nomes[users][0] + ", "
    broadcast(messageCurr[:-2])
    return

#faz a saida do chat pelo usuário que enviou o comando bye e indica para todos quem saiu
def leave_room(ip_port_tuple):
    nome = dic_Nomes.pop(ip_port_tuple)
    broadcast(nome[0] + " saiu da sala!")
    return
    
#faz boradcast para todos os clientes
def broadcast(message):
    for ip_port_tuple in dic_Nomes:
        rdt_send_message(message, ip_port_tuple)        
    return

# retorna uma string formatada com hora da mensagem e usuário 
def format_message(message, ip_port_tuple):
    curr_time = datetime.datetime.now()
    curr_time = curr_time.strftime("%H:%M:%S")
    user_name = dic_Nomes[ip_port_tuple][0]
    return curr_time + " " + user_name + ": " + message
    

while True:
    # 1o de tudo: o servidor não faz NADA até receber alguma mensagem. Só depois de receber qualquer mensagem vamos ver o que ela significa

    try:
        message, ip_port_tuple = rdt_receive_message()
        #print(message)

        if ip_port_tuple not in dic_Nomes:
            if message[:16] == "hi, meu nome eh ":
                add_user_to_list(message[16:], ip_port_tuple)
                print(str(message[16:]) + " entrou na sala!") # para debugar
                broadcast(message[16:] + " entrou na sala!")
        
        # Agora que recebeu a mensagem, vamos observar do que se trata

        elif message == "list":
            broadcast(format_message(message, ip_port_tuple))
            send_user_list(ip_port_tuple)
        
        elif message == "bye":
            broadcast(format_message(message, ip_port_tuple))
            leave_room(ip_port_tuple)
        
        else:
            broadcast(format_message(message, ip_port_tuple))
    
    except timeout:
        print('', end = '', sep='')
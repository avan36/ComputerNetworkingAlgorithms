
import socket
import sys
import time
import random

#Setting up socket
host = 'localhost'
port = 50008
try :
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error:
      print("Failed to create socket")
      sys.exit()
print("Created server sock")

#Binding socket
try:
    server_sock.bind((host, port))
except socket.error:
     print("Failed to bind socket")
     sys.exit()

print("Socket now bound to host and port")

checker = True
while checker: 
    #Receiving messages
    try:
        bin_data, addr = server_sock.recvfrom(1024)
        
    except socket.error:
        print("Error receiving")

        
    time_received = time.time()
    data = bin_data.decode('utf-8')
    print("Data time received: " + str(time_received))
    
    
    
    #Sending back
    randomnum = int(random.random() * 10)
    if randomnum != 1:
        bin_data = data.encode('utf-8')
        server_sock.sendto(bin_data, addr)
        print("Relayed message")
    else:
        print("SIMULATING dropped packet")
    



import socket
import sys
import time
from datetime import datetime

try: 
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error:
    print("Failed to create socket")
    sys.exit()

host = 'localhost'
port = 50008

checker = True
server_sock.settimeout(5)
while checker: 

        for i in range(10):
            start = time.time()
            protocolheader = "msg: " + str(i) + "\n"
            data = "A"
            send_data = protocolheader + data
            bin_data = send_data.encode('utf-8')
            data_received = False
            #Sending
            try:
                server_sock.sendto(bin_data, (host,port))
            except socket.error:
                print("Error sending")
           
            print("Message sent")
            
            #Receiving
            try:
                binreply, addr = server_sock.recvfrom(1024)
                strreply = binreply.decode('utf-8')
                protocolheader, timereceived = strreply.split('\n')
                #Checking if this is right message
                if protocolheader == "msg: " + str(i):
                    data_received = True
                    end = time.time()
                    #Printing results
                    end_to_end_time = end - start
                    start_converted = datetime.fromtimestamp(start)
                    formatted_time = start_converted.strftime('%A, %B, %d, %Y %H: %M:%S')
                    print("Reply from " + str(addr[0]) + ": PING " + str(i) + " " + formatted_time)
                    print("RTT: " + str(end_to_end_time))
            #Handling time out
            except socket.error:
                print("Request timed out")
        checker = False
   







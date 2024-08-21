
import socket
import struct
import sys
import time
import json
host = 'localhost'

class DistanceVector():
    def __init__(self, router_list: list, port: int, num_routers: int, num_nbrs: int):
        self.routing_table = {}
        self.neighbor_costs = {}
        self.port = int(port)
        self.num_routers = num_routers
        self.num_nbrs = num_nbrs
        self.timeout = 10
        for i in range(0, len(router_list), 2):
            x = int(router_list[i])
            y = int(router_list[i+1]) if (i + 1) < len(router_list) else None
            self.routing_table[x] = y
            self.neighbor_costs[x] = y
        print("Initialized routing table:", self.routing_table)
        self.run()

    #UPDATING VALUES FUNCTION
    def update_values(self, received, port_received_from):
        current = self.routing_table
        combined_keys = list(set(list(self.routing_table.keys()) + list(received.keys())))
        for i in combined_keys:
            if i == self.port:
                continue
            elif i in received and i not in current.keys():
                if port_received_from in current.keys():
                    current[i] = received[i] + current[port_received_from]
                else:
                    print("No connection found between", i, "and", self.port)
            elif i in current.keys() and i not in received:
                continue
            elif i in received.keys() and i in current.keys():
                current[i] = min(self.routing_table[i], received[i] + current[port_received_from])
            
        return current


    def run(self):
        #MARK: PACKET CREATION
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
        except OSError:
            print ("Unable to allocate socket")
            sys.exit(0)
        
        #MARK: BINDING
        try:
            sock.bind((host, self.port))
        except socket.error:
            print("Failed to bind socket")
            sys.exit()

        #MARK: RECEIVING AND SENDING
        checker = True
        while checker:
            try:
                binreply, addr = sock.recvfrom(1024)
                strreply = binreply.decode('utf-8')
                strreply = json.loads(strreply)
                strreply = {int(key): int(value) for key, value in strreply.items()}
                port_received_from = int(addr[1])
                self.routing_table = self.update_values(strreply, port_received_from)
                print("Distance vector for node", self.port)
                print(self.routing_table)
                time.sleep(1)
            except socket.error:
                    print("Nothing received. Timed out.")
            
            for dest in self.neighbor_costs.keys():
                try:
                    str_data = json.dumps(self.routing_table)
                    bin_data = str_data.encode('utf-8')
                    sock.sendto(bin_data, (host,int(dest)))
                except socket.error:
                    print("Error sending")
            
            time.sleep(2)
            

        
def main():
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
        num_routers = int(sys.argv[2])
        num_nbrs = int(sys.argv[3])
        print("Number of routers: ", num_routers)
        print("Number of neighbors: ", num_nbrs)

        router_list = sys.argv[4:]
        router_list = list(map(int, router_list))
        print("Running")
        distance_vector = DistanceVector(router_list, port, num_routers, num_nbrs)
        
    

if __name__ == '__main__':
    main()


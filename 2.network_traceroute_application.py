#!/usr/bin/python3
import socket
import struct
import sys
import time
import ipaddress

class IcmpTraceroute():

    def __init__(self, src_ip, dst_ip, ip_id, ip_ttl, icmp_id, icmp_seqno):

        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.ip_id = ip_id
        self.max_ttl = ip_ttl
        self.ip_ttl = 1
        self.icmp_id = icmp_id
        self.icmp_seqno = icmp_seqno

    def checksum(self, header):
        sum = 0
        for i in range(0, len(header), 2):
            a = header[i]
            b = header[i + 1]
            b = b << 8
            
            toAdd = a + b
            sum = sum + toAdd
        
        #Managing Overflow
        overflow = sum >> 16
        sum = sum & 0xffff
        sum = sum + overflow

        overflow = sum >> 16
        sum = sum & 0xffff
        sum = sum + overflow

        sum = ~sum & 0xffff

        sum2 = sum &0xff
        sum1 = sum >> 8
        sum2 = sum2 << 8
        sum = sum2 + sum1
        
        return sum
         

    def run_traceroute(self):
        # Create packet
        ip_header = self.create_ip_header(None)
        ip_header_checksum = self.checksum(ip_header)
        ip_header = self.create_ip_header(ip_header_checksum)
        icmp_header = self.create_icmp_header(None)
        icmp_header_checksum = self.checksum(icmp_header)
        icmp_header = self.create_icmp_header(icmp_header_checksum)

        #Need to count for overflow
        bin_echo_req = ip_header + icmp_header


        # Create send and receive sockets
        send_sock = socket.socket(
                socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        recv_sock = socket.socket(
                socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)

        # Set IP_HDRINCL flag so kernel does not rewrite header fields
        send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

        # Set receive socket timeout to 2 seconds
        try:
            recv_sock.settimeout(2.0)

            # Send packet to destination
            send_sock.sendto(bin_echo_req, (self.dst_ip, 0))
            start = time.time()
            # Receive icmp reply (hopefully)
            [bin_echo_reply, addr] = recv_sock.recvfrom(1024)
            end = time.time()
            difference = end - start

            # Extract info from ip_header
            [ip_header_length, ip_identification, ip_protocol,
                    ip_src_addr]  = self.decode_ip_header(bin_echo_reply)

            # Extract info from icmp_header
            [icmp_type, icmp_code] = self.decode_icmp_header(
                    bin_echo_reply, ip_header_length)
        
            print(str(self.ip_ttl) + " " + str(ip_src_addr), str(round(difference * 1000)) + " ms")
            self.ip_ttl = self.ip_ttl + 1

            if self.ip_ttl <= 64:
                if ip_src_addr != '8.8.8.8':
                    self.run_traceroute()
                else:
                    print("Reached destination.")
        except:
            print("Timed out.")
            if self.ip_ttl <= 64:
                
                self.ip_ttl = self.ip_ttl + 1
                print("Increasing TTL to " + str(self.ip_ttl))
                self.run_traceroute()
        
    def create_ip_header(self, checksum):
        # Returned IP header is packed binary data in network order
        ip_version = 4
        ip_IHL = 5
        combined_version_IHL = 69
        ip_type_of_service = 0
        ip_total_length = 20
        ip_identification = self.ip_id
        ip_flags_ip_fragment_offset = 0
        ip_ttl = self.ip_ttl
        ip_protocol = 1

        if checksum is not None:
            ip_header_checksum = checksum

        else:
            ip_header_checksum = 0
        
        ip_source_address = socket.inet_aton(self.src_ip)
        ip_destination_address = socket.inet_aton(self.dst_ip)
        ip_header = struct.pack('!BBHHHBBH4s4s', # ! means network order
        combined_version_IHL,  #B          
        ip_type_of_service, #B
        ip_total_length,  #H
        ip_identification, #H
        ip_flags_ip_fragment_offset, #H
        ip_ttl, #B
        ip_protocol,#B
        ip_header_checksum, #H
        ip_source_address, #L
        ip_destination_address,#L
        )
        
        return ip_header

    def create_icmp_header(self, checksum):

        ECHO_REQUEST_TYPE = 8
        ECHO_CODE = 0

        # ICMP header info from https://tools.ietf.org/html/rfc792
        icmp_type = ECHO_REQUEST_TYPE      # 8 bits
        icmp_code = ECHO_CODE              # 8 bits
        if checksum is not None:
            icmp_checksum = checksum
        else:
            icmp_checksum = 0
        icmp_identification = self.icmp_id # 16 bits
        icmp_seq_number = self.icmp_seqno  # 16 bits

        # ICMP header is packed binary data in network order
        icmp_header = struct.pack('!BBHHH', # ! means network order
        icmp_type,           # B = unsigned char = 8 bits
        icmp_code,           # B = unsigned char = 8 bits
        icmp_checksum,       # H = unsigned short = 16 bits
        icmp_identification, # H = unsigned short = 16 bits
        icmp_seq_number)     # H = unsigned short = 16 bits

        return icmp_header

    def decode_ip_header(self, bin_echo_reply):
        unprocessed_length = bin_echo_reply[0]
        ip_header_length = unprocessed_length & 0x0F
        ip_header_length = ip_header_length
        
        # Decode ip_header
        if len(bin_echo_reply) < 20:
            print("Incomplete IP header. ", len(bin_echo_reply), "bytes received.")
            return None
        unpacked = struct.unpack('!BBHHHBBH4s4s', bin_echo_reply[:20])

        # Extract fields of interest
        unprocessed_length = unpacked[0]
        ip_identification = unpacked[3]
        ip_protocol = unpacked[6]
        ip_src_addr = socket.inet_ntoa(unpacked[8])

        #Unprocessed is now a binary number
        return [ip_header_length, ip_identification,
                ip_protocol, ip_src_addr]


    def decode_icmp_header(self, bin_echo_reply, ip_header_length):
        # Decode icmp_header
        unpacked = struct.unpack('!BBHHH',bin_echo_reply[ip_header_length:ip_header_length + 8])

        # Extract fields of interest
        icmp_type = unpacked[0] # Should equal 11, for Time-to-live exceeded
        icmp_code = unpacked[1] # Should equal 0
        return [icmp_type, icmp_code]

def main():

    src_ip = '172.21.1.106' # Your IP addr (e.g., IP address of VM) #hostname -I
    dst_ip = '8.8.8.8' #'42.210.226.43'     # Destination IP address
    #8.8.8.8
    ip_id = 111             # IP header in wireshark should have
    ip_ttl = 64             # Max TTL
    icmp_id = 222           # ICMP header in wireshark should have
    icmp_seqno = 1          # Starts at 1, by convention

    if len(sys.argv) > 1:
        src_ip = sys.argv[1]
        dst_ip = sys.argv[2]
        ip_id = int(sys.argv[3]) #arv
        ip_ttl = int(sys.argv[4])
        icmp_id = int(sys.argv[5])
        icmp_seqno = int(sys.argv[6])
    
    traceroute = IcmpTraceroute(
            src_ip, dst_ip, ip_id, ip_ttl, icmp_id, icmp_seqno)
    print("Traceroute to", str(dst_ip), ip_ttl, "hops max")
    traceroute.run_traceroute()

if __name__ == '__main__':
    main()


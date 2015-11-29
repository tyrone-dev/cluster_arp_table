# tutorial on python multicasting

# receiver side

__author__ = "Tyrone van Balla"
__version__= "Version 1.0.0"
__descripito__ = "Cluster ARP Table Generator: Slave Node"

import socket
import struct
import sys
from uuid import getnode as get_mac
import json
import fcntl

# function to find ip of specified interface
def get_ip_address(ifname):
    dummy_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        dummy_sock.fileno(),
        0x8915,
        struct.pack('256s', ifname[:15])
        )[20:24])

ifname = 'eth0'

multicast_group = '224.3.29.71'
server_address = ('', 10000)

# get IP address
ip_addr = get_ip_address(ifname)

# get hostname
hostname = socket.gethostname()

# get MAC address (in usual hex format as string)
mac_addr = ':'.join(("%012X" % get_mac())[i:i+2] for i in range(0, 12, 2))

# create list of slave information and serialize to string for sending
slave_info =  (hostname, ip_addr, mac_addr)
slave_info_string = json.dumps(slave_info)

# create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# bind socket to the server address
sock.bind(server_address)

# add the socket to the multicast group
group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# UDP echo client receiver
while True:
    print "\nWaiting to receive message . . . "
    data, address = sock.recvfrom(1024)

    print "Received {} bytes from {}".format(len(data), address)
    
    #print data
    
    try:
        print "Sending slave node data to {} . . .".format(address)
        sock.sendto(slave_info_string, address)
        print "Done"
        break
    except:
        print "Error sending data to master node"

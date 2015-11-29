# tutorial on python multicasting 

# sender side

__author__ = "Tyrone van Balla"
__version__ = "Version 1.0.0"
__description__ = "Cluster ARP Table Generator: Master Node"

import socket
import struct
import sys
import argparse
import json
import threading
import fcntl
from uuid import getnode as get_mac

# TODO: add argparse for number of nodes, make compulsory
# TODO: write arp table to file
# TODO: replace all print debug with logging
# TODO: add logging for thread as well
# TODO: add docstring

# function to find ip of specified interface
def get_ip_address(ifname):
    dummy_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        dummy_sock.fileno(),
        0x8915,
        struct.pack('256s', ifname[:15])
        )[20:24])

ifname = 'eth0'

# send "hello" packets continuously
# thread used to send packets continuously
# thread is stopped when all nodes are successfully connected or on timout
def say_hello(master_socket, message, multicast_group, stop_event):
    while (not stop_event.isSet()):
        sent = master_socket.sendto(message, multicast_group)

    print "Exiting ping packet thread . . ."

hello_thread_stop = threading.Event()

message = ". . . Cluster Master Node . . ."

multicast_group = ('224.3.29.71', 10000)

# get master node info

# host name
hostname = socket.gethostname()

# MAC address
mac_addr = ':'.join(("%012X" % get_mac())[i:i+2] for i in range(0, 12, 2))

# IP address
ip_addr = get_ip_address(ifname)

master_info = [hostname, ip_addr, mac_addr]

# create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# set a timeout value to prevent socket from blocking indefinitely
sock.settimeout(10)

# set number of nodes in cluster
nodes = 3

# basic UDP echo client

connected = 0

# create list to hold each slave node's data
slaves = []

# create list to hold all node data
cluster_info = []

try:

    # send data to MCast group
    #sent  = sock.sendto(message, multicast_group)
    hello_thread = threading.Thread(target=say_hello, args=(sock, message, multicast_group, hello_thread_stop,))
    hello_thread.start()
    
    # listen for responses from all recipients
    while (connected < nodes - 1):
        
        # send data to MCast group
        # sent  = sock.sendto(message, multicast_group)
        
        print "Waiting to receive . . ."
        try:
            data, server = sock.recvfrom(1024)
        except socket.timeout:
            print "Timed out, no more responses"
            print "Only {} nodes active".format(connected + 1)
            break
        else:
            print "Received {} from {}".format(data, server)
            print "Node Connected"
            slaves.append(json.loads(data))
            connected += 1

    # all nodes connected, stop sending "hello" packet
    hello_thread_stop.set()
    if (connected + 1 == nodes):
        print "All nodes active. ARP Table created for cluster"

finally:
    print "Closing socket . . ."
    sock.close()
    
# generate list of all nodes in cluster
cluster_info.append(master_info)
cluster_info.extend(sorted(slaves))
print cluster_info

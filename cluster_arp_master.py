#!/usr/bin/ python

# Raspberry Pi Cluster ARP Table Generator

# Master Node / sender side

# docstring
"""
Cluster ARP Generator for Master Node.

Sends out probe packets looking for slaves.
Waits for response and then generates ARP Table for
all nodes in cluster.
"""

__author__ = "Tyrone van Balla"
__version__ = "Version 1.0.0"
__description__ = "Cluster ARP Table Generator: Master Node"

import socket
import argparse
import json
import threading
import logging

import interface_info
import send_email

# email info
to_user = 'misa.stuff01@gmail.com'
from_user = to_user
password = 'misaisreallycute'

def say_hello(master_socket, message, multicast_group, stop_event):
    """
    Send probe packets to look for slave.
    Separate thread is used to send these packets continuously
    """
    
    # thread stops when all nodes are connected or on timeout
    while (not stop_event.isSet()):
        sent = master_socket.sendto(message, multicast_group)

    logger.debug("Exiting ping packet thread . . .")

def create_arp_table(cluster_info, cluster_name, filename):
    """
    Create ARP Table by parsing list containing all node information.
    Writes the table a file. 
    """

    logger.debug("Creating new file for arp table.")
    arp_file = open(filename, 'w')
    arp_file.write("Cluster ARP Table: {}\n\n".format(cluster_name))
    
    for node in cluster_info:
        arp_file.write("Hostname: %-*s IP Address: %-*s MAC Address: %-*s\n" % (18, node[0], 18, node[1], 18, node[2]))

    logger.debug("ARP Table file created")
    arp_file.close()
    logger.debug("File closed.")
    
    return

def create_master_info(master_ip, num_nodes, filename):
    """
    Create a file containing master ip address and
    number of nodes online in cluster.

    Info to be sent later via serial comms
    """
    
    logger.debug("Creating core info file")
    core_info_file = open(filename, 'w')
    core_info_file.write("Master IP:\n{}\nNodes: {}\n".format(master_ip, num_nodes))

    logger.debug("Core info file created")
    core_info_file.close()
    logger.debug("core info file closed")

    return

if __name__ == '__main__':
    # argument parser
    parser = argparse.ArgumentParser(description="Generate ARP Table for a Raspberry Pi Cluster\nMaster Node")

    parser.add_argument("nodes", help="Specify the number of nodes in the cluster", type=int) # compulsory argument

    parser.add_argument("-s", "--sleep", help="Specify sleep time if running on boot", type=int) 

    #parser.add_argument("-m", "--multicast", help="Specify multicast group address", default="224.3.29.71")
    parser.add_argument("-p", "--port", help="Specify broadcast group port", type=int, default=10000)

    parser.add_argument("-n", "--name", help="Specify a name for the cluster", default="__katherine cluster__")

    parser.add_argument("-i", "--interface", help="Specify which network interface to use", default="eth0") # default interface is eth0)
    parser.add_argument("-e", "--external", help="Specificy which network interface to use for the external network IF multiple interfaces on master", default=None)
    parser.add_argument("-t", "--timeout", help="Specify timeout in seconds for waiting for connections from nodes", type=int, default=10)
    parser.add_argument("-f", "--filename", help="Specify filename to write ARP Table to", default="cluster_arp_table")
    parser.add_argument("-q", "--quiet", help="Enable flag to not send email with ARP Table", action="store_true")
    parser.add_argument("-v", "--verbosity", help="Incease output verbosity", action="count", default=0)
    
    parser.add_argument("-r", "--rfid", help="Enable RFID reader", action="store_true")

    args = parser.parse_args()
    
    # logger
    logger = logging.getLogger("Master_Node_ARP")

    if args.verbosity == 0:
        level = logging.INFO
    else:
        level = logging.DEBUG
        
    logger.setLevel(level)

    # file handler
    fh = logging.FileHandler("master_arp_log.log")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(threadName)s  - %(levelname)s -%(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    if args.sleep:
        logger.debug("Going to sleep . . . ")
        import time
        time.sleep(args.sleep)
    
    hello_thread_stop = threading.Event()

    message = ". . . Cluster Master Node . . ."

    #multicast_group = (args.multicast, args.port) - use multicast if not on isolated network

    # create list of all interfaces on master

    interfaces = [args.interface, args.external]
    interfaces = [x for x in interfaces if x != None]
    iface_info = []
    
    # get master node info
    for iface in interfaces:
        master = interface_info.Interface(iface)
        iface_info.append(master)
    
    master_info = [iface_info[0].hostname, iface_info[0].ip_addr, iface_info[0].mac_addr]
    master_found_info = [master_info]
    
    # create identifer for external interface
    if args.external != None:
        master_ext_info = [iface_info[1].hostname + "_ext", iface_info[1].ip_addr, iface_info[1].mac_addr]
        master_found_info.append(master_ext_info)
    
    # create broadcast group address

    broadcast_group = master_info[1].split('.')
    broadcast_group[3] = '255'
    broadcast_group = ['.'.join(broadcast_group)]
    broadcast_group.append(10000)
    broadcast_group = tuple(broadcast_group)
    
    # create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # set options: broadcast
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # set a timeout value to prevent socket from blocking indefinitely
    sock.settimeout(args.timeout)

    # set number of nodes in cluster
    nodes = args.nodes

    # basic UDP echo client

    connected_nodes = 0

    # create list to hold each slave node's data
    slaves = []

    # create list to hold all node data
    cluster_info = []

    try:

        # send data to broadcast group
        #sent  = sock.sendto(message, multicast_group)
        hello_thread = threading.Thread(name="Hello Packets", target=say_hello, args=(sock, message, broadcast_group, hello_thread_stop,))
        hello_thread.start()
        
        # listen for responses from all recipients
        while (connected_nodes < nodes - 1):
            
            # send data to MCast group
            # sent  = sock.sendto(message, multicast_group)
            
            logger.debug("Waiting to receive . . .")
            try:
                data, server = sock.recvfrom(1024)
            except socket.timeout:
                logger.warning("Timed out, no more responses")
                logger.info("Only {} nodes active".format(connected_nodes + 1))
                break
            else:
                logger.info("Received {} from {}".format(data, server))
                logger.debug("Node Connected")
                slaves.append(json.loads(data))
                connected_nodes += 1

        # all nodes connected, stop sending "hello" probe packet
        hello_thread_stop.set()
        if (connected_nodes + 1 == nodes):
            logger.debug("All nodes active. ARP Table created for cluster")

    finally:
        logger.debug("Closing socket . . .")
        sock.close()

    # create core info file
    create_master_info(master.ip_addr, connected_nodes + 1, "core_info")
    
    # generate list of all nodes in cluster
    for iface in master_found_info:
        cluster_info.append(iface)
    
    cluster_info.reverse()    
    cluster_info.extend(sorted(slaves))

    # create arp file
    create_arp_table(cluster_info, args.name, args.filename)
    
    # check quiet mode flag (no email)
    if not args.quiet:
        logger.info("Sending ARP Table via email . . . ")
        try:
            send_email.send_email(args.filename, args.name, to_user, from_user, password)
            logger.debug("ARP Table successfully sent")
        except:
            logger.error("Sending ARP Table failed")

    # for rfid control
    if args.rfid:
        logger.info("Starting RFID Loop . . . ")
        
        import serial
        ser = serial.Serial('/dev/ttyACM0', 9600)

        while True:
            data = ser.readline().strip('\x00')
            
            if (data == 'authorized\r\n'):
                # send email
                try:
                    send_email.send_email(args.filename, args.name, to_user, from_user, password)
                    logger.debug("ARP Table successfully sent - via RFID")
                    ser.write("Email Sent")
                except:
                    logger.error("Sending ARP Table failed - via RFID")
            else:
                # do nothing
                ser.write("Unauthorized!")
                logger.warning("Unauthorized access attempted!")

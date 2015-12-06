#!/usr/bin/env python

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
import interface_info
import logging

# TODO: write arp table to file
# TODO: send arp table via email
# TODO: add quiet mode check

def say_hello(master_socket, message, multicast_group, stop_event):
    """
    Send probe packets to look for slave.
    Separate thread is used to send these packets continuously
    """
    
    # thread stops when all nodes are connected or on timeout
    while (not stop_event.isSet()):
        sent = master_socket.sendto(message, multicast_group)

    logger.debug("Exiting ping packet thread . . .")

if __name__ == '__main__':
    # argument parser
    parser = argparse.ArgumentParser(description="Generate ARP Table for a Raspberry Pi Cluster\nMaster Node")

    parser.add_argument("nodes", help="Specify the number of nodes in the cluster", type=int) # compulsory argument

    parser.add_argument("-m", "--multicast", help="Specify multicast group address", default="224.3.29.71")
    parser.add_argument("-p", "--port", help="Specifcy multicast group port", type=int, default=10000)


    parser.add_argument("-i", "--interface", help="Specify which network interface to use", default="eth0") # default interface is eth0)
    parser.add_argument("-t", "--timeout", help="Specify timeout in seconds for waiting for connections from nodes", type=int, default=10)
    parser.add_argument("-f", "--filename", help="Specify filename to write ARP Table to", default="pi_cluster_arp")
    parser.add_argument("-q", "--quiet", help="Enable flag to not send email with ARP Table", action="store_true")
    parser.add_argument("-v", "--verbosity", help="Incease output verbosity", action="count", default=0)

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

    hello_thread_stop = threading.Event()

    message = ". . . Cluster Master Node . . ."

    multicast_group = (args.multicast, args.port)

    # get master node info

    master = interface_info.Interface(args.interface)

    master_info = [master.hostname, master.ip_addr, master.mac_addr]

    # create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

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

        # send data to MCast group
        #sent  = sock.sendto(message, multicast_group)
        hello_thread = threading.Thread(name="Hello Packets", target=say_hello, args=(sock, message, multicast_group, hello_thread_stop,))
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

    # generate list of all nodes in cluster
    cluster_info.append(master_info)
    cluster_info.extend(sorted(slaves))

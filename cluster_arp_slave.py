#!/usr/bin/env python

# Raspberry Pi Cluster ARP Table Generator

# Slave Node/ Receiver side

# docstring
"""
Cluster ARP Generator for Slave Node.

Waits for probe packet from master node;
then sends slave hostname, ip address and mac address
to master.
"""

__author__ = "Tyrone van Balla"
__version__= "Version 1.0.0"
__description__ = "Cluster ARP Table Generator: Slave Node"

import socket
import struct
import json
import argparse
import interface_info
import logging

if __name__ == '__main__':
    # argument parser
    parser = argparse.ArgumentParser(description="Generate ARP Table for a Raspberry Pi Cluster\nSlave Node")

    parser.add_argument("-i", "--interface", help="Specify which network interface to use", default="eth0") # default interface is eth0)
    parser.add_argument("-m", "--multicast", help="Specify multicast group address", default="224.3.29.71")
    parser.add_argument("-p", "--port", help="Specify multicast group port", type=int, default=10000)
    
    parser.add_argument("-s", "--sleep", help="Specify time to sleep", type=int)

    parser.add_argument("-t", "--timeout", help="Specify timeout in seconds for waiting for connections from nodes" , type=int, default=None)

    parser.add_argument("-v", "--verbosity", help="Incease output verbosity", action="count", default=0)

    args = parser.parse_args()

    # logger
    logger = logging.getLogger("Slave_Node_ARP")

    if args.verbosity == 0:
        level = logging.INFO
    else:
        level = logging.DEBUG

    logger.setLevel(level)

    # file handler
    fh = logging.FileHandler("slave_arp_log.log")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    server_address = ('', args.port)

    if args.sleep:
        logger.debug("Going to sleep for a bit")
        import time
        time.sleep(args.sleep)
    
    # get node info
    node = interface_info.Interface(args.interface)

    # create list of slave information and serialize to string for sending
    slave_info =  (node.hostname, node.ip_addr, node.mac_addr)
    slave_info_string = json.dumps(slave_info)

    # create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # set timeout
    sock.settimeout(args.timeout)

    # bind socket to the server address
    sock.bind(server_address)

    # add the socket to the multicast group
    group = socket.inet_aton(args.multicast)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    # UDP echo client receiver
    while True:
        logger.debug("Waiting to receive message . . . ")
        try:    
            data, address = sock.recvfrom(1024)

            logger.info("Received {} bytes from Master at: {}".format(len(data), address))
        
        except socket.timeout:
            logger.warning("Timed out, no response")
            break
        
        try:
            logger.info("Sending slave node data to Master at: {} . . .".format(address))
            sock.sendto(slave_info_string, address)
            logger.debug("Slave data sent to Master node")
            break
        except:
            logger.error("Error sending data to master node")

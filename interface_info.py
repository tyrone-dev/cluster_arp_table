# Get network information of host and create object
    # hostname
    # ip address (for interface)
    # mac address (for interface)

import socket
import struct
import fcntl
from uuid import getnode as get_mac

class Interface (object):

    # create dummy socket for finding IP and MAC
    dummy_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # intitialize object
    def __init__(self, interface):
        self.interface = interface
        self.hostname = self.get_hostname()
        self.ip_addr = self.get_ip_addr(self.interface)
        self.mac_addr = self.get_mac_addr(self.interface)

    # find hostname
    def get_hostname(self):
        return socket.gethostname()

    # find mac address and format in AA:BB:CC:DD:EE:FF
    def get_mac_addr(self, ifname):
        
        """
        the method below fails if:
        there are multiple NICs on a host
        there are no NICs on a host
        """
        #return ':'.join(("%012X" % get_mac())[i:i+2] for i in range(0, 12, 2))
        """
        the method below works in all cases
        """

        info = fcntl.ioctl(self.dummy_sock.fileno(), 0x8927,  struct.pack('256s', ifname[:15]))
        return ':'.join(['%02X' % ord(char) for char in info[18:24]])

    # find ip address of specified interface
    def get_ip_addr(self, ifname):
        
        return socket.inet_ntoa(fcntl.ioctl(
            self.dummy_sock.fileno(),
            0x8915,
            struct.pack('256s', ifname[:15])
            )[20:24])

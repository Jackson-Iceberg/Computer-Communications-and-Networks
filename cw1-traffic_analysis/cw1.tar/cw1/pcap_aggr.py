from scapy.utils import RawPcapReader
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP
from ipaddress import ip_address, ip_network
import sys
import matplotlib.pyplot as plt

class Node(object):
    def __init__(self, ip, plen):
        self.bytes = plen
        self.left = None
        self.right = None
        self.ip = ip
    def add(self, ip, plen):
        if self.ip == ip: # same ip, add it.
            self.bytes += plen
        elif self.ip > ip:
            if self.left: # if it has left node, add it into left node.
                self.left.add(ip,plen)
            else:   # Create a new left Node
                self.left = Node(ip_address(ip),plen)
        elif self.ip < ip:
            if self.right: # if it has right node, add it into right node.
                self.right.add(ip,plen)
            else:  # Create a new right Node
                self.right = Node(ip_address(ip),plen)

    def data(self, data):
        if self.left:
            self.left.data(data)
        if self.bytes > 0:
            data[ip_network(self.ip)] = self.bytes
        if self.right:
            self.right.data(data)
    @staticmethod 
    def supernet(ip1, ip2):
        na1 = ip_network(ip1).network_address
        na2 = ip_network(ip2).network_address
        int_na1 = int(na1)
        int_na2 = int(na2)
        binary_1 = bin(int_na1)[2:].zfill(32) # to 32 bits binary 
        binary_2 = bin(int_na2)[2:].zfill(32) # to 32 bits binary
        netmask = 0
        common_binary = ''
        while netmask < 32 and binary_1[netmask] == binary_2[netmask]:
            common_binary += binary_1[netmask]
            netmask = netmask + 1 # get the number of same binary
        if common_binary == '':
            common_address = 0 # no common binary means common address = 0
        else:
            common_address = int(common_binary, 2) * (2 ** (32 - netmask)) # enlarge the common address 
        na1 = str(ip_address(common_address))
        return ip_network('{}/{}'.format(na1, netmask), strict=False)

    def aggr(self, byte_thresh):
        if self.left != None:
            self.left.aggr(byte_thresh) # recursion post-order
            if self.left.bytes < byte_thresh:
                self.bytes += self.left.bytes # aggregate bytes & set it as supernet.
                self.ip = Node.supernet(self.ip, self.left.ip)  
                self.left.bytes = 0 
                if self.left.left == None and self.left.right == None: # if both left node and right node are null, then delete
                    self.left = None 
        if self.right != None:
            self.right.aggr(byte_thresh) 
            if self.right.bytes < byte_thresh:
                self.bytes += self.right.bytes 
                self.ip = Node.supernet(self.ip, self.right.ip)
                self.right.bytes = 0 
                if self.right.left == None and self.right.right == None:
                    self.right  = None 
        

            
class Data(object):
    def __init__(self, data):
        self.tot_bytes = 0
        self.data = {}
        self.aggr_ratio = 0.05
        root = None
        cnt = 0
        for pkt, metadata in RawPcapReader(data):
            ether = Ether(pkt)
            if not 'type' in ether.fields:
                continue
            if ether.type != 0x0800:
                continue
            ip = ether[IP]
            self.tot_bytes += ip.len
            if root is None:
                root = Node(ip_address(ip.src), ip.len)
            else:
                root.add(ip_address(ip.src), ip.len)
            cnt += 1
        root.aggr(self.tot_bytes * self.aggr_ratio)
        root.data(self.data)
    def Plot(self):
        data = {k: v/1000 for k, v in self.data.items()}
        plt.rcParams['font.size'] = 8
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.grid(which='major', axis='y')
        ax.tick_params(axis='both', which='major')
        ax.set_xticks(range(len(data)))
        ax.set_xticklabels([str(l) for l in data.keys()], rotation=45,
            rotation_mode='default', horizontalalignment='right')
        ax.set_ylabel('Total bytes [KB]')
        ax.bar(ax.get_xticks(), data.values(), zorder=2)
        ax.set_title('IPv4 sources sending {} % ({}KB) or more traffic.'.format(
            self.aggr_ratio * 100, self.tot_bytes * self.aggr_ratio / 1000))
        plt.savefig(sys.argv[1] + '.aggr.pdf', bbox_inches='tight')
        plt.close()
    def _Dump(self):
        with open(sys.argv[1] + '.aggr.data', 'w') as f:
            f.write('{}'.format({str(k): v for k, v in self.data.items()}))

if __name__ == '__main__':
    d = Data(sys.argv[1])
    d.Plot()
    d._Dump()

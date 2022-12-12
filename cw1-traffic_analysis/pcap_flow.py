from scapy.utils import RawPcapReader
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, TCP
from scapy.layers.inet6 import IPv6
from ipaddress import ip_address, IPv6Address
from socket import IPPROTO_TCP
import sys
import matplotlib.pyplot as plt

class Flow(object):
    def __init__(self, data):
        self.pkts = 0
        self.flows = 0
        self.ft = {}
        for pkt, metadata in RawPcapReader(data):
            self.pkts += 1
            ether = Ether(pkt)
            if ether.type == 0x86dd:
                ip = ether[IPv6]
                if(ip.nh != 6):
                    continue # Skip when Next Header field in the IPv6 header does not indicate TCP
                src_ip = int(IPv6Address(ip.src))
                dst_ip = int(IPv6Address(ip.dst))
                byte_length = ip.plen
                
            elif ether.type == 0x0800:
                ip = ether[IP]
                if(ip.proto != 6):
                    continue # Skip when Protocol field in the IPv4 header is not TCP
                src_ip = int(ip_address(ip.src))
                dst_ip = int(ip_address(ip.dst))
                byte_length = ip.len - ip.ihl*4 # delete the IPv4 IHL (Internet Header Length)

            try: # Ignore packets in which Scapy does not recognize the TCP header.
                tcp = ip[TCP]
                src_port = tcp.sport
                dst_port = tcp.dport
                byte_length = byte_length - tcp.dataofs*4 # delete dataoffset in TCP

                if (src_ip,dst_ip,src_port,dst_port) in self.ft:
                    self.ft[src_ip,dst_ip,src_port,dst_port] += byte_length
                elif (dst_ip,src_ip,dst_port,src_port) in self.ft:
                    self.ft[dst_ip,src_ip,dst_port,src_port] += byte_length
                else:
                    self.ft[src_ip,dst_ip,src_port,dst_port] = byte_length
                    self.flows += 1
            except:
                continue

    def Plot(self):
        topn = 100
        data = [i/1000 for i in list(self.ft.values())]
        data.sort()
        data = data[-topn:]
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        ax.hist(data, bins=50, log=True)
        ax.set_ylabel('# of flows')
        ax.set_xlabel('Data sent [KB]')
        ax.set_title('Top {} TCP flow size distribution.'.format(topn))
        plt.savefig(sys.argv[1] + '.flow.pdf', bbox_inches='tight')
        plt.close()
    def _Dump(self):
        with open(sys.argv[1] + '.flow.data', 'w') as f:
            f.write('{}'.format(self.ft))

if __name__ == '__main__':
    d = Flow(sys.argv[1])
    d.Plot()
    d._Dump()

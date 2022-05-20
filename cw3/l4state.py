from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_4
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import in_proto
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp
from ryu.lib.packet.ether_types import ETH_TYPE_IP

class L4State14(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_4.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(L4State14, self).__init__(*args, **kwargs)
        self.ht = set()

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def features_handler(self, ev):
        dp = ev.msg.datapath
        ofp, psr = (dp.ofproto, dp.ofproto_parser)
        acts = [psr.OFPActionOutput(ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER)]
        self.add_flow(dp, 0, psr.OFPMatch(), acts)

    def add_flow(self, dp, prio, match, acts, buffer_id=None):
        ofp, psr = (dp.ofproto, dp.ofproto_parser)
        bid = buffer_id if buffer_id is not None else ofp.OFP_NO_BUFFER
        ins = [psr.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, acts)]
        mod = psr.OFPFlowMod(datapath=dp, buffer_id=bid, priority=prio,
                                match=match, instructions=ins)
        dp.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        in_port, pkt = (msg.match['in_port'], packet.Packet(msg.data))
        dp = msg.datapath
        ofp, psr, did = (dp.ofproto, dp.ofproto_parser, format(dp.id, '016d'))
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        # get IP header and TCP header
        ipHeader = pkt.get_protocols(ipv4.ipv4)
        tcpHeader = pkt.get_protocols(tcp.tcp)

        # if in_port == 1: out_port = 2
        # else: out_port = 1
        out_port = 2 if in_port == 1 else 1

        acts = [psr.OFPActionOutput(out_port)] # intialize acts 
        
        # non-TCP-over-IPv4 packets
        con = len(tcpHeader) == 0 or len(ipHeader) == 0
        if con:
            acts = [psr.OFPActionOutput(out_port)]
        # TCP over IPv4 packets
        else:
            ip_src = ipHeader[0].src
            ip_dst = ipHeader[0].dst
            src_port = tcpHeader[0].src_port
            dst_port = tcpHeader[0].dst_port
            
            # from port 1
            if in_port == 1:
                match = (ip_src,ip_dst,src_port,dst_port)
                if tcpHeader[0].has_flags(tcp.TCP_SYN, tcp.TCP_RST) or tcpHeader[0].has_flags(tcp.TCP_SYN, tcp.TCP_FIN) or tcpHeader[0].bits == 0:
                    acts = [psr.OFPActionOutput(ofp.OFPPC_NO_FWD)]

                else:
                    acts = [psr.OFPActionOutput(out_port)]
                    if match is not None and match not in self.ht:
                        self.ht.add(match)
                    mtc = psr.OFPMatch(in_port=in_port,eth_type=eth.ethertype,ipv4_src=ip_src,ipv4_dst = ip_dst,ip_proto = ipHeader[0].proto,tcp_src=src_port,tcp_dst=dst_port)
                    bufferID = msg.buffer_id
                    self.add_flow(dp,1,mtc,acts,bufferID)
                    if bufferID  != ofp.OFP_NO_BUFFER:
                        return  
      
            # from port 2
            elif in_port == 2:
                match = (ip_dst,ip_src,dst_port,src_port)
                if match not in self.ht:
                    acts = [psr.OFPActionOutput(ofp.OFPPC_NO_FWD)] # drop the packet
                else:
                    acts = [psr.OFPActionOutput(out_port)]
                    mtc = psr.OFPMatch(in_port=in_port,eth_type=eth.ethertype,ipv4_src=ip_src,ipv4_dst = ip_dst,ip_proto = ipHeader[0].proto,tcp_src=src_port,tcp_dst=dst_port)
                    bufferID = msg.buffer_id
                    self.add_flow(dp,1,mtc,acts,bufferID)
                    if bufferID  != ofp.OFP_NO_BUFFER:
                        return

        data = msg.data if msg.buffer_id == ofp.OFP_NO_BUFFER else None
        out = psr.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
                               in_port=in_port, actions=acts, data=data)
        dp.send_msg(out)

# Hao Zhou s18623223
from socket import *
import sys 
import math
import time

class Sender2(object):
    
    def __init__(self,ip,port,fileToSend,timeOut):
        # get remote host as arg1
        self.UDP_IP = ip
        # get port number
        self.UDP_PORT = int(port)
        # fileToSend
        self.fileToSend = fileToSend
        #set up socket
        self.sender_socket = socket(AF_INET, SOCK_DGRAM)
        # Open the file to convert to a binary array
        with open(fileToSend, 'rb') as f: 
            fr = f.read()
            self.image = bytearray(fr)
        
        # initialize
        self.image_size = len(self.image)
        self.packet_number = math.ceil(self.image_size/1024)
        self.sender_socket.settimeout(int(timeOut)/1000)
        self.start_time = None
        self.end_time = None
        self.retransmission = 0
        
        

    def result(self):
        throughput =  self.image_size/(self.end_time-self.start_time)
        print(self.retransmission)
        print(throughput/1000)

    def getPacket(self,sendACK,EOF,start,end):
        packet = bytearray()
        packet.extend(sendACK.to_bytes(2,byteorder='big'))
        packet.append(EOF)
        packet.extend(self.image[start:end])
        return packet

    def sendPacket(self,packet):
        self.sender_socket.sendto(packet,(self.UDP_IP,self.UDP_PORT))
    
    def checkPacket(self,EOF,ack_list,packet,receivACK):
        # check return ACK and send ACK
        packetCorrect = False
        while(packetCorrect == False):  
            try:
                data,address = self.sender_socket.recvfrom(2)
                receivACK = int.from_bytes(data[0:2],byteorder='big')
                if(receivACK not in ack_list):
                    packetCorrect = True
                    ack_list.append(receivACK)
                if(receivACK == self.packet_number):
                    break
    
            except timeout:
                if(EOF == 1 and receivACK == self.packet_number):
                    break

                self.sendPacket(packet)
                self.retransmission+=1        


    def send(self):
        # initialize 
        start = 0
        end = 1024
        sendACK = 1
        receivACK = 0
        EOF = 0
        self.start_time = time.time()
        ack_list = []
        for index in range(self.packet_number+1):
            if(index == self.packet_number):
                EOF = 1
            
            # packet to send
            packet = self.getPacket(sendACK,EOF,start,end)
            self.sendPacket(packet)
            # print("sendACk:{0}".format(sendACK))
            # check packet is correct or not
            self.checkPacket(EOF,ack_list,packet,receivACK)
            sendACK+=1
            start+=1024
            end+=1024
        
        # all the packet have been sent. check the time and print. close the socket.
        self.end_time = time.time()
        self.sender_socket.close()
        self.result()


if __name__ == '__main__':
    sender = Sender2(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])
    sender.send()


            # for index in range(self.packet_number+1):
            #     if(index == self.packet_number):
            #     EOF = 1
            
            # # packet to send
            # packet = self.getPacket(sendACK,EOF,start,end)
            # self.sendPacket(packet)
            # # print("sendACk:{0}".format(sendACK))
            # # check packet is correct or not
            # self.checkPacket(EOF,ack_list,packet,receivACK)
            # sendACK+=1
            # start+=1024
            # end+=1024
# Hao Zhou s18623223
from socket import *
import sys 
import math
import time



class Sender1(object):
    
    def __init__(self,ip,port,fileToSend):
        # get remote host as arg1
        self.UDP_IP = ip
        # geet port number
        self.UDP_PORT = int(port)
        # fileToSend
        self.fileToSend = fileToSend
        #set up socket
        self.sender_socket = socket(AF_INET,SOCK_DGRAM) 
        # Open the file to convert to a binary array
        with open(fileToSend, 'rb') as f: 
            fr = f.read()
            self.image = bytearray(fr)
        
        # initialize
        self.image_size = len(self.image)
        self.packet_number = math.ceil(self.image_size/1024)
        self.final_packet = self.image_size % 1024



    def send(self):
        # initialize 
        start = 0
        end = 1024
        sequenceNumber = 0
        EOF = 0

        # image size smaller than 1kb
        if(end >= self.image_size):
            EOF = 1
            packet = bytearray(3+self.image_size)
            packet.extend(sequenceNumber.to_bytes(2,byteorder='big'))
            packet.append(EOF)
            packet.extend(self.image[start:self.image_size])
            self.sender_socket.sendto(packet,(self.UDP_IP,self.UDP_PORT))

        # image size greater than 1kb
        for index in range(self.packet_number):
            if(end == self.image_size):
                EOF = 1
            packet = bytearray()
            packet.extend(sequenceNumber.to_bytes(2,byteorder='big'))
            packet.append(EOF)
            packet.extend(self.image[start:end])
            self.sender_socket.sendto(packet,(self.UDP_IP,self.UDP_PORT))

            sequenceNumber +=1
            start += 1024
            end +=1024
            time.sleep(0.00001)

        if(self.final_packet != 0):
            # sequenceNumber += 1
            EOF = 1
            packet = bytearray()
            packet.extend(sequenceNumber.to_bytes(2,byteorder='big'))
            packet.append(EOF)
            packet.extend(self.image[start:self.image_size])
            self.sender_socket.sendto(packet,(self.UDP_IP,self.UDP_PORT))

        self.sender_socket.close()



if __name__ == '__main__':
    sender = Sender1(sys.argv[1],sys.argv[2],sys.argv[3])
    sender.send()
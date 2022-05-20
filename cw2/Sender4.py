# Hao Zhou s18623223
import sys
from socket import *
from threading import *
import time
import math

class Sender4(object):
    def __init__(self,ip, port, fileToSend, timeOut, windowSize):
         # get remote host as arg1
        self.UDP_IP = ip
        # get port number
        self.UDP_PORT = int(port)
        # fileToSend
        self.fileToSend = fileToSend
        #set up socket
        self.sender_socket = socket(AF_INET, SOCK_DGRAM)
        self.sender_socket.bind((self.UDP_IP,self.UDP_PORT+1))
        #set up timeOut
        self.timeOut = int(timeOut)
        # Open the file to convert to a binary array
        with open(fileToSend, 'rb') as f: 
            fr = f.read()
            self.image = bytearray(fr)
        # initialize
        self.image_size = len(self.image)
        self.packet_number = math.ceil(self.image_size/1024)
        self.start_time = 0
        self.end_time = 0
        self.windowSize = int(windowSize)
        self.baseNum = 0
        self.seqNum = 0
        self.curr_packet = None

        self.end = False
        # Windows to save the packets that has been made.
        self.windows = {}
        # Buffer to store confirmed ACKs
        self.confirmed_ack = {}
        

    def getPacket(self,EOF):
        packet = bytearray()
        packet.extend(self.seqNum.to_bytes(2,byteorder='big'))
        packet.append(EOF)
        packet.extend(self.image[1024 * self.seqNum: 1024 * (self.seqNum+ 1)])
        return packet
    
    def updateWindow(self,packet):
        self.windows[self.seqNum] = packet

    def getPacketFromWindow(self,seqNum):
        return self.windows.get(seqNum)

    def byteToInt(self,data):
        return int.from_bytes(data, byteorder='big', signed=False)

    # receive returned ACK from receiver
    def receiveACK(self):
        while True:
            data, address = self.sender_socket.recvfrom(2048)
            receivACK = self.byteToInt(data)

            # if the ACK have received, set the corresponding entry  as 1
            # 1 indicates this ACK has been received
            if receivACK not in self.confirmed_ack.keys():
                self.confirmed_ack[receivACK] = 1
                # update baseNum
                while self.baseNum in self.confirmed_ack.keys():
                    self.baseNum += 1

    def sendPacket(self,packet):
        self.sender_socket.sendto(packet,(self.UDP_IP, self.UDP_PORT))

    # send packet and start timer
    def send_pktThread(self, seqNum):
        send = True
        while send:
            packet = self.getPacketFromWindow(seqNum)
            self.sendPacket(packet)

            # if send is True, the packets will resend
            timeOut = False
            # sleep to check if the ACK is received, if not received: return True 
            time.sleep(self.timeOut / 1000)
            if self.confirmed_ack.get(seqNum) is None:
                timeOut = True
            send = timeOut


    def send(self):
        # thread to receive the ACKs from receiver
        thread = Thread(target=self.receiveACK)
        thread.daemon = True
        thread.start()
        EOF = 0
        # record start time
        self.start_time = math.ceil(time.time() * 1000)

        # while not all packets is successfully sent to receiver
        while self.baseNum < self.packet_number:

            if self.seqNum == self.packet_number -1:
                EOF = 1
            
            # if there is still space in the window, send the packet
            if self.seqNum < self.baseNum + self.windowSize and self.seqNum < self.packet_number:
                # get the pacekt via windows
                if(self.seqNum in self.windows.keys()):
                    packet = self.getPacketFromWindow(self.seqNum)
                    self.curr_packet = packet
                    
                else:
                    packet = self.getPacket(EOF)
                    self.updateWindow(packet)
                    self.curr_packet = packet
               
                seq = self.seqNum

                # start a thread to send the packet 
                thread2 = Thread(target=self.send_pktThread,args=[seq])
                thread2.daemon = True
                thread2.start()

                # update the sequence number
                self.seqNum += 1

        # record end time of sending process
        self.end_time = math.ceil(time.time() * 1000)

      # get the result
    def result(self):
        timeTaken = (self.end_time - self.start_time)/1000
        print(self.packet_number / timeTaken)


if __name__ == '__main__':

    sender = Sender4(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])
    sender.send()
    sender.result()

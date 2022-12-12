# Hao Zhou s18623223
import sys
from socket import *
from threading import *
import time
import math

class Sender3(object):
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
        #set up timeout
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
        # Windows to save the packets that has been made.
        self.windows = {}
        # current packet to send
        self.curr_packet = None
        self.timer = False
        self.last_time = 0



    # invoke this function via thread, keep receiving the ACk from receiver socket.
    def receivACK(self):
        while True:
            data, address = self.sender_socket.recvfrom(2048)
            self.baseNum = self.byteToInt(data) + 1

            if self.baseNum == self.seqNum:
                self.timer = False

            # restart the timer and update timer's started time
            else:
                self.timer = True
                self.last_time = math.ceil(time.time() * 1000)
        
    def byteToInt(self,data):
        return int.from_bytes(data, byteorder='big', signed=False)

    def getPacket(self,EOF):
        packet = bytearray()
        packet.extend(self.seqNum.to_bytes(2,byteorder='big'))
        packet.append(EOF)
        packet.extend(self.image[1024 * self.seqNum: 1024 * (self.seqNum+ 1)])
        return packet
    
    def updateWindow(self,packet):
        self.windows[self.seqNum] = packet

    def getPacketFromWindow(self):
        return self.windows.get(self.seqNum)

    def sendPacket(self,packet):
        self.sender_socket.sendto(packet,(self.UDP_IP, self.UDP_PORT))

    def overTimeChecker(self,curr_time):
        timeSpend = curr_time - self.last_time
        if(timeSpend>self.timeOut):
                return True
        return False

    def send(self):
        # record start time
        self.start_time = math.ceil(time.time() * 1000)
        # start a new thread
        thread = Thread(target=self.receivACK)
        thread.daemon = True
        thread.start()
        EOF = 0

        while self.baseNum < self.packet_number:

            overTime = False
            if self.seqNum == self.packet_number -1:
                EOF = 1

            # check over time
            curr_time = math.ceil(time.time() * 1000)
            overTime = self.overTimeChecker(curr_time)

            # timer is open and overTime. Set back to base sequence number
            if self.timer and overTime:
                self.seqNum = self.baseNum

            # check the windows space
            if self.seqNum < self.baseNum + self.windowSize and self.seqNum < self.packet_number:
                
                # get the pacekt via windows
                if(self.seqNum in self.windows.keys()):
                    packet = self.getPacketFromWindow()
                    self.curr_packet = packet
                    self.sendPacket(packet)
                
                else:
                    packet = self.getPacket(EOF)
                    self.updateWindow(packet)
                    self.curr_packet = packet
                    self.sendPacket(packet)

                # baseNumber equals seq number, start the timer
                if self.baseNum == self.seqNum:
                    self.timer = True
                    self.last_time = math.ceil(time.time() * 1000)

                self.seqNum += 1               
              
        # record end time
        self.end_time = math.ceil(time.time() * 1000)
        self.result()

    # get the result
    def result(self):
        timeTaken = (self.end_time - self.start_time)/1000
        print(self.packet_number / timeTaken)

if __name__ == '__main__':
    sender3 = Sender3(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])
    sender3.send()


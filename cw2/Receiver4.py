# Hao Zhou s18623223
from socket import *
import sys 

class Receiver4(object):
    
    def __init__(self,port,fileToStore,windowSize):
        # localhost
        self.UDP_IP = "127.0.0.1"
        # port
        self.UDP_PORT = int(port)
        # get file
        self.filename = fileToStore
        # windowSize
        self.windowSize = int(windowSize)
        self.windows = {}
        # initialize socket
        self.receiver_socket = socket(AF_INET,SOCK_DGRAM)
        self.receiver_socket.bind((self.UDP_IP,self.UDP_PORT))
        self.image = bytearray()
        self.currACK = -1
        self.expected_ACK = 0
        self.base = 0
        # print("check initization")
        
    
    def saveFile(self):
        with open(self.filename,'wb') as f:
            f.write(self.image)
    
    def getACK(self,data):
        receiACK = int.from_bytes(data[0:2],byteorder='big')
        return receiACK

    # def sendACK(self,ACK,address):
    #     sendACK = ACK.to_bytes(2,byteorder='big')
    #     self.receiver_socket.sendto(sendACK,address)
    
    # def byteToInt(self,data):
    #     return int.from_bytes(data, byteorder='big', signed=False)

    # def sendPacket(self,packet):
    #     self.receiver_socket.sendto(packet,(self.UDP_IP, self.UDP_PORT))

    # def getElement(self,ACK):
    #     return self.windows[ACK]


    def store_send(self):
        try:
            while True:
                data, clientAddress = self.receiver_socket.recvfrom(2048)
                receivACK = self.getACK(data)

                # if receving window still have spaces, process the received packet, if not, do nothing.
                end_of_window = self.base + self.windowSize 
                if self.base <= receivACK and receivACK < end_of_window:

                    if self.expected_ACK == receivACK:
                        self.windows[receivACK] = data[3:1027]
                        while self.windows.get(self.expected_ACK) is not None:
                            self.image += self.windows.get(self.expected_ACK)
                            self.expected_ACK += 1
                            self.base += 1
                            self.saveFile()
                        
                    # if not, put the received packet into  windows
                    else:
                        self.windows[receivACK] = data[3:1027]

                # send ACK 
                self.ACK = data[0:2]
                self.receiver_socket.sendto(self.ACK, clientAddress)
                self.receiver_socket.settimeout(10)
                
        except Exception:
            self.receiver_socket.close()


if __name__ == '__main__':
    receiver = Receiver4(sys.argv[1],sys.argv[2],sys.argv[3])
    receiver.store_send()
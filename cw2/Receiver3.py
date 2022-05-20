# Hao Zhou s18623223
from socket import *
import sys 

class Receiver3(object):
    
    def __init__(self,port,fileToStore):
        # localhost
        self.UDP_IP = "127.0.0.1"
        # port
        self.UDP_PORT = int(port)
        # get file
        self.filename = fileToStore
        # initialize socket
        self.receiver_socket = socket(AF_INET,SOCK_DGRAM)
        self.receiver_socket.bind((self.UDP_IP,self.UDP_PORT))
        self.image = bytearray()
        self.currACK = -1
        self.expected_ACK = 0
        
    
    def saveFile(self):
        with open(self.filename,'wb') as f:
            f.write(self.image)
    
    def getACK(self,data):
        receiACK = int.from_bytes(data[0:2],byteorder='big')
        return receiACK

    def sendACK(self,ACK,address):
        sendACK = ACK.to_bytes(2,byteorder='big')
        self.receiver_socket.sendto(sendACK,address)

    def store_send(self):
        state = True
        try:   
            while state:
                
                data,address = self.receiver_socket.recvfrom(2048)
                receiACK = self.getACK(data)
                EoF = data[2]
                if(self.expected_ACK == receiACK):
                    self.image += data[3:1027]
                    self.saveFile()
                    self.currACK = self.expected_ACK
                    self.expected_ACK += 1
                    if(EoF==1):
                        state = False
                
                if self.currACK != -1:
                    self.sendACK(self.currACK,address)
                
                self.receiver_socket.settimeout(9)
        except Exception:
            self.receiver_socket.close()

if __name__ == '__main__':
    receiver = Receiver3(sys.argv[1],sys.argv[2])
    receiver.store_send()

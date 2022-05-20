# Hao Zhou s18623223
from socket import *
import sys 

class Receiver1(object):

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

    def store(self):

        state = True
        while state:
            data,address = self.receiver_socket.recvfrom(1027)
            sequence_number = int.from_bytes(data[:2],'big')
            EoF = data[2]
            self.image+=data[3:]
            if (EoF == 1): 
                state = False

        with open(self.filename,'wb') as f:
            f.write(self.image)

        self.receiver_socket.close()


if __name__ == '__main__':
    receiver = Receiver1(sys.argv[1],sys.argv[2])
    receiver.store()
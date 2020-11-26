import socket


class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = socket.gethostname()
        self.port = 5555
        self.addr = (self.server, self.port)
        self.pos = self.connect()

    def getPos(self):
        return self.pos

    def connect(self):
        print('Trying to connect to server....')
        try:
            self.client.connect(self.addr)
            print("CONNECTED TO SERVER:", self.server)
            return self.client.recv(2048).decode()
        except:
            print("COULD NOT CONNECT TO SERVER:", self.server)

    def send(self, data):
        try:
            self.client.send(str.encode(data))
            return self.client.recv(2048).decode()
        except socket.error as e:
            print(e)
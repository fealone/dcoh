class RWSocket(object):

    def __init__(self, sock):
        self.sock = sock
        self.send = sock.send
        self.recv = sock.recv
        self.write = sock.send
        self.read = sock.recv

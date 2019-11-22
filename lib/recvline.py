class Recvline(object):

    def __init__(self, sockobj, windowsize=10240):
        self.sockobj = sockobj
        self.windowsize = windowsize
        self.block = self.sockobj.recv(self.windowsize)
        self.sended_size = 0

    def recvline(self):
        self.chunk = None
        self.terminator = None
        if b"\r\n" in self.block:
            chunk, terminator, self.block = self.block.partition(b"\r\n")
            return chunk + terminator
        self.sockobj.setblocking(0)
        try:
            self.block += self.sockobj.recv(self.windowsize-len(self.block))
        except Exception:
            pass
        else:
            self.recvline()
        finally:
            self.sockobj.setblocking(1)

    def recv(self, size):
        if len(self.block) >= size:
            result = self.block[0:size]
            self.block = self.block[size-1:]
            yield result
            return
        self.sended_size = len(self.block)
        while 1:
            self.block = self.sockobj.recv(self.windowsize)
            if self.sended_size + len(self.block) >= size:
                send_size = size - self.sended_size
                result = self.block[0:send_size]
                self.block = self.block[send_size-1:]
                self.sended_size += len(result)
                yield result
                return
            self.sended_size += len(self.block)
            result = self.block
            self.block = b""
            yield result

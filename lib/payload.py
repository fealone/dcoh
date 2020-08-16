from lib import recvline


class PayloadIterator(object):

    def __init__(self, recvobj: recvline.Recvline, size: int):
        self.recvobj = recvobj
        self.size = size
        self.byte = 0

    def __iter__(self) -> "PayloadIterator":
        return self

    def __next__(self) -> bytes:
        if self.byte == self.size:
            raise StopIteration()
        raw = next(self.recvobj.recv(self.size))
        if raw:
            self.byte += len(raw)
            return raw
        else:
            raise StopIteration()

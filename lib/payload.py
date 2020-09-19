from typing import Optional

from lib import recvline


class PayloadIterator(object):

    def __init__(self, recvobj: recvline.Recvline, size: Optional[int]):
        self.recvobj = recvobj
        self.size = size
        self.byte = 0

    def __iter__(self) -> "PayloadIterator":
        return self

    def __next__(self) -> bytes:
        if self.size and self.byte == self.size:
            raise StopIteration()
        raw = next(self.recvobj.recv(self.size))
        if raw:
            self.byte += len(raw)
            return raw
        else:
            raise StopIteration()

class ContentObject(object):

    def __init__(self, res, *args, **kwargs):
        self.res = res
        self.buf = bytearray()
        self.pos = 0
        self.stream_reader = self.stream()
        self.previous_chunk = bytearray()
        self.seekable = False
        self.writable = False
        self.finished = False

    def size(self):
        raise NotImplementedError()

    def stream(self):
        yield b""

    def read(self, size=None):
        while not self.finished:
            try:
                if len(self.buf) < size:
                    self.buf += next(self.stream_reader)
            except StopIteration:
                if len(self.buf) < size:
                    self.finished = True
            if size:
                if len(self.buf) >= size:
                    chunk = self.buf[:size]
                    del self.buf[:size]
                    self.pos += size
                    self.previous_chunk = chunk
                    return bytes(chunk)
                continue
        self.pos += len(self.buf)
        chunk = self.buf[:]
        del self.buf[:]
        self.previous_chunk = chunk
        return bytes(chunk)

    def close(self):
        self.finished = True

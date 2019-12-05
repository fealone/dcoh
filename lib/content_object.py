class ContentObject(object):

    def __init__(self, res, *args, **kwargs):
        self.res = res
        self.buf = bytearray()
        self.pos = 0
        self.stream_reader = self.stream()
        self.seekable = False
        self.writable = False
        self.finished = False

    def size(self):
        raise NotImplementedError()

    # Override this property if you need to change the headers.
    @property
    def headers(self):
        return self.res.headers

    # Override this property if you need to change the status code.
    @property
    def status_code(self):
        return self.res.status_code

    def stream(self):
        yield b""

    def read(self, size=None):
        while 1:
            try:
                if len(self.buf) < size:
                    self.buf += next(self.stream_reader)
            except StopIteration:
                if len(self.buf) < size:
                    break
            if size:
                if len(self.buf) >= size:
                    chunk = self.buf[:size]
                    del self.buf[:size]
                    self.pos += size
                    size = hex(len(bytes(chunk))
                            ).split("0x")[1].upper().encode("utf-8")
                    return size + b"\r\n" + bytes(chunk) + b"\r\n"
                continue
        if self.buf:
            self.pos += len(self.buf)
            chunk = self.buf[:]
            del self.buf[:]
            size = hex(len(bytes(chunk))
                    ).split("0x")[1].upper().encode("utf-8")
            return size + b"\r\n" + bytes(chunk) + b"\r\n"
        elif self.finished:
            return None
        else:
            self.finished = True
            return b"0\r\n\r\n"

    def close(self):
        self.finished = True

from typing import Any, Dict, Generator, Optional

import requests


class ContentObject(object):

    def __init__(self, res: requests.Response, request_headers: Dict[str, str]) -> None:
        self.res = res
        self.request_headers = request_headers
        self.buf = bytearray()
        self.pos = 0
        self.stream_reader = self.stream()
        self.seekable = False
        self.writable = False
        self.finished = False

    # Override this method if you need to set the content size.
    def size(self) -> Optional[int]:
        return None

    # Override this property if you need to change the headers.
    @property
    def headers(self) -> Any:
        return self.res.headers

    # Override this property if you need to change the status code.
    @property
    def status_code(self) -> int:
        return self.res.status_code

    def stream(self) -> Generator[bytes, None, None]:
        yield b""

    def read(self, size: Optional[int] = None) -> Optional[bytes]:
        content_size = self.size()
        while 1:
            if size:
                try:
                    if len(self.buf) < size:
                        self.buf += next(self.stream_reader)
                except StopIteration:
                    if len(self.buf) < size:
                        break
                if len(self.buf) >= size:
                    chunk = self.buf[:size]
                    del self.buf[:size]
                    self.pos += size
                    size_h = hex(len(bytes(chunk))).split("0x")[1].upper().encode("utf-8")
                    if content_size is None:
                        return size_h + b"\r\n" + bytes(chunk) + b"\r\n"
                    else:
                        return chunk
                continue
        if self.buf:
            self.pos += len(self.buf)
            chunk = self.buf[:]
            del self.buf[:]
            size_h = hex(len(bytes(chunk))).split("0x")[1].upper().encode("utf-8")
            if content_size is None:
                return size_h + b"\r\n" + bytes(chunk) + b"\r\n"
            else:
                return chunk
        elif self.finished:
            return None
        else:
            self.finished = True
            return b"0\r\n\r\n"

    def close(self) -> None:
        self.finished = True

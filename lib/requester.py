import logging
import os
import shutil
import socket
import io
from importlib import machinery
from typing import Any, Dict, List, Tuple

from lib import payload, rwsocket, recvline

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("requester")


class Requester(object):

    def __init__(self, secure: bool = False):
        self.session = requests.Session()
        self.secure = secure

    def request(self, target: str, headers: Dict[str, Any], recvobj: recvline.Recvline) -> Tuple[Any, Any]:
        if self.secure:
            protocol = "https"
        else:
            protocol = "http"
        host = target.split(":")[0]
        filename = headers['url'].split("?")[0].split("#")[0].split(".")[0]
        request_payload = None
        if "content-length" in headers["header"] and headers["header"]["content-length"] != "0":
            try:
                size = int(headers["header"]["content-length"])
                recvobj = payload.PayloadIterator(recvobj, size)
                if os.path.exists(f"contents/{host}{filename}.py"):
                    loader = machinery.SourceFileLoader(filename, f"contents/{host}{filename}.py")
                    module = loader.load_module(filename)
                    if module.ResponseObject.need_request_payload:  # type: ignore
                        request_payload = b"".join(list(recvobj))
                        recvobj = io.BytesIO(request_payload)
                req = requests.Request(headers["method"],
                                       f"{protocol}://{target}{headers['url']}",
                                       headers=headers["header"],
                                       data=recvobj)
                prepared = req.prepare()
                if "Transfer-Encoding" in prepared.headers:
                    del prepared.headers["Transfer-Encoding"]
                res = self.session.send(prepared, stream=True, allow_redirects=False)
            except Exception:
                logger.warning(f"Cannot connect to {target}")
                return None, None
        else:
            try:
                req = requests.Request(headers["method"],
                                       f"{protocol}://{target}{headers['url']}",
                                       headers=headers["header"])
                prepared = req.prepare()
                if "content-length" in prepared.headers:
                    del prepared.headers["content-length"]
                res = self.session.send(prepared, stream=True, allow_redirects=False)
            except Exception:
                logger.warning(f"Cannot connect to {target}")
                return None, None
        return res, request_payload

    def response(self,
                 client: socket.socket,
                 res: requests.Response,
                 source: List[str],
                 headers: Dict[str, Any],
                 request_payload: bytes) -> None:
        host = source[0]
        rw_client = rwsocket.RWSocket(client)
        suffix = ""
        if headers["url"].endswith("/"):
            suffix = "index.html"
        filename = headers['url'].split("?")[0].split("#")[0].split(".")[0]
        if os.path.exists(f"contents/{host}{filename}.py"):
            logger.info(f"Selected script with [contents/{host}{filename}.py]")
            try:
                loader = machinery.SourceFileLoader(filename, f"contents/{host}{filename}.py")
                module = loader.load_module(filename)
                res_obj = module.ResponseObject(res, headers["header"], request_payload)  # type: ignore
                content_size = res_obj.size()
                res.headers = res_obj.headers
                res.status_code = res_obj.status_code
                if content_size:
                    res.headers["Content-Length"] = str(content_size)
                    if "Transfer-Encoding" in res.headers:
                        del res.headers["Transfer-Encoding"]
                else:
                    res.headers["Transfer-Encoding"] = "chunked"
                    if "Content-Length" in res.headers:
                        del res.headers["Content-Length"]
            except Exception:
                logger.warning((f"Occurred error in "
                                f"[contents/{host}{filename}.py]"),
                               exc_info=True)
                res_obj = res.raw
            set_cookies = ""
            if "Set-Cookie" in res.headers:
                for cookie in res.headers["Set-Cookie"].split(", "):
                    set_cookies += f"Set-Cookie: {cookie}\r\n"
                del res.headers["Set-Cookie"]
            res_header = '\r\n'.join('{}: {}'.format(
                k, v) for k, v in res.headers.items())
            res_headers = (f"HTTP/1.1 {res.status_code}\r\n"
                           f"{res_header}\r\n"
                           f"{set_cookies}\r\n")
            rw_client.send(res_headers.encode("utf-8"))
            shutil.copyfileobj(res_obj, rw_client)
        elif os.path.exists(f"contents/{host}{headers['url']}{suffix}"):
            logger.info((f"Selected content with "
                         f"[contents/{host}{headers['url']}{suffix}]"))
            if "Content-Encoding" in res.headers:
                del res.headers["Content-Encoding"]
            content_size = os.path.getsize(f"contents/{host}{headers['url']}{suffix}")
            res.headers["Content-Length"] = str(content_size)
            set_cookies = ""
            if "Set-Cookie" in res.headers:
                for cookie in res.headers["Set-Cookie"].split(", "):
                    set_cookies += f"Set-Cookie: {cookie}\r\n"
                del res.headers["Set-Cookie"]
            res_header = '\r\n'.join('{}: {}'.format(
                k, v) for k, v in res.headers.items())
            res_headers = (f"HTTP/1.1 {res.status_code}\r\n"
                           f"{res_header}\r\n"
                           f"{set_cookies}\r\n")
            rw_client.send(res_headers.encode("utf-8"))
            f = open(f"contents/{host}{headers['url']}{suffix}", "rb")
            hole = open("/dev/null", "ab")
            shutil.copyfileobj(f, rw_client)
            shutil.copyfileobj(res.raw, hole)
        else:
            set_cookies = ""
            if "Set-Cookie" in res.headers:
                for cookie in res.raw.headers.getlist("Set-Cookie"):
                    set_cookies += f"Set-Cookie: {cookie}\r\n"
                del res.headers["Set-Cookie"]
            res_header = '\r\n'.join('{}: {}'.format(
                k, v) for k, v in res.headers.items())
            res_headers = (f"HTTP/1.1 {res.status_code}\r\n"
                           f"{res_header}\r\n"
                           f"{set_cookies}\r\n")
            rw_client.send(res_headers.encode("utf-8"))
            shutil.copyfileobj(res.raw, rw_client)

    def delegate(self,
                 client: socket.socket,
                 recvobj: recvline.Recvline,
                 target: str,
                 headers: Dict[str, Any]) -> bool:
        res, request_payload = self.request(target, headers, recvobj)
        if res is None:
            return False
        if "Transfer-Encoding" in res.headers:
            del res.headers["Transfer-Encoding"]
        host = target.split(":")
        try:
            self.response(client, res, host, headers, request_payload)
        except Exception:
            logger.warning(f"Cannot response error. {target}")
            return False
        if res.headers.get("Connection") == "close":
            return False
        return True

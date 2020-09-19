from importlib import machinery
import logging
import os
import shutil
import socket
from typing import Any, Dict, List, Optional, Tuple

from lib import payload, recvline, rwsocket
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("requester")


class Requester(object):

    def __init__(self, secure: bool = False):
        self.session = requests.Session()
        self.secure = secure

    def has_request_payload(self, header: Dict[str, str]) -> Tuple[bool, Optional[int]]:
        if "content-length" in header and header["content-length"] != "0":
            return True, int(header["content-length"])
        if "transfer-encoding" in header and header["transfer-encoding"] == "chunked":
            return True, None
        return False, None

    def request(self, target: str, headers: Dict[str, Any], recvobj: recvline.Recvline) -> Tuple[Any, Any]:
        if self.secure:
            protocol = "https"
        else:
            protocol = "http"
        delegator = None
        host, port = target.split(":")
        if port in ["80", "443"]:
            request_target = host
        else:
            request_target = target
        filename = headers['url'].split("?")[0].split("#")[0].split(".")[0]
        has_payload, payload_size = self.has_request_payload(headers["header"])
        if os.path.exists(f"contents/{host}{filename}.py"):
            logger.info(f"Selected script with [contents/{host}{filename}.py]")
            loader = machinery.SourceFileLoader(filename, f"contents/{host}{filename}.py")
            module = loader.load_module(filename)
            delegator = module.Delegate()  # type: ignore
            if has_payload:
                request_payload = payload.PayloadIterator(recvobj, payload_size)
                delegator.set_request_payload(request_payload)
            delegator.set_headers(headers)
            delegator.set_target(target)
            delegator.set_protocol(protocol)
            try:
                req = delegator.get_request()
                prepared = req.prepare()
                if "content-length" in prepared.headers:
                    if "Transfer-Encoding" in prepared.headers:
                        del prepared.headers["Transfer-Encoding"]
                res = self.session.send(prepared, stream=True, allow_redirects=False)
            except Exception:
                logger.warning(f"Cannot connect to {target} because exception in custom script", exc_info=True)
                return None, None
        else:
            if has_payload:
                request_payload = payload.PayloadIterator(recvobj, payload_size)
                req = requests.Request(headers["method"],
                                       f"{protocol}://{request_target}{headers['url']}",
                                       headers=headers["header"],
                                       data=request_payload)
                prepared = req.prepare()
            else:
                req = requests.Request(headers["method"],
                                       f"{protocol}://{request_target}{headers['url']}",
                                       headers=headers["header"])
                prepared = req.prepare()
            try:
                if "content-length" in prepared.headers:
                    if "Transfer-Encoding" in prepared.headers:
                        del prepared.headers["Transfer-Encoding"]
                res = self.session.send(prepared, stream=True, allow_redirects=False)
            except Exception:
                logger.warning(f"Cannot connect to {request_target}")
                return None, None
        return res, delegator

    def response(self,
                 client: socket.socket,
                 res: requests.Response,
                 source: List[str],
                 headers: Dict[str, Any],
                 delegator: Any) -> None:
        host = source[0]
        rw_client = rwsocket.RWSocket(client)
        suffix = ""
        if headers["url"].endswith("/"):
            suffix = "index.html"
        filename = headers['url'].split("?")[0].split("#")[0].split(".")[0]
        if delegator:
            try:
                res_obj = delegator.get_response(res)
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
            except AttributeError:
                res_obj = res.raw
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
        res, delegator = self.request(target, headers, recvobj)
        if res is None:
            return False
        if "Transfer-Encoding" in res.headers:
            del res.headers["Transfer-Encoding"]
        host = target.split(":")
        try:
            self.response(client, res, host, headers, delegator)
        except Exception:
            logger.debug(f"Cannot response error. {target}")
            return False
        if res.headers.get("Connection") == "close":
            return False
        return True

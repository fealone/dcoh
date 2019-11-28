import logging
import os
import shutil
from importlib import machinery

from lib import payload, rwsocket

import requests

logger = logging.getLogger("requester")


class Requester(object):

    def __init__(self, secure=False):
        self.session = requests.Session()
        self.secure = secure

    def request(self, target, headers, recvobj):
        if self.secure:
            protocol = "https"
        else:
            protocol = "http"
        host = target.split(":")[0]
        if "content-length" in headers["header"]:
            try:
                size = int(headers["header"]["content-length"])
                req = requests.Request(
                        headers["method"],
                        f"{protocol}://{host}{headers['url']}",
                        headers=headers["header"],
                        data=payload.PayloadIterator(
                            recvobj,
                            size))
                prepared = req.prepare()
                if "Transfer-Encoding" in prepared.headers:
                    del prepared.headers["Transfer-Encoding"]
                res = self.session.send(
                        prepared,
                        stream=True,
                        allow_redirects=False,
                        )
            except Exception:
                logger.warning(f"Cannot connect to {target}")
        else:
            try:
                req = requests.Request(
                        headers["method"],
                        f"{protocol}://{target}{headers['url']}",
                        headers=headers["header"])
                prepared = req.prepare()
                if "content-length" in prepared.headers:
                    del prepared.headers["content-length"]
                res = self.session.send(
                        prepared,
                        stream=True,
                        allow_redirects=False,
                        )
            except Exception:
                logger.warning(f"Cannot connect to {target}")
        return res

    def response(self, client, res, host, headers):
        host = host[0]
        rw_client = rwsocket.RWSocket(client)
        suffix = ""
        if headers["url"].endswith("/"):
            suffix = "/index.html"
            headers["url"] = headers["url"].rstrip("/")
        filename = "/" + headers['url'].split(".")[0]
        if os.path.exists(f"contents/{host}{filename}.py"):
            try:
                loader = machinery.SourceFileLoader(
                        filename,
                        f"contents/{host}{filename}.py")
                module = loader.load_module()
                if "Content-Encoding" in res.headers:
                    del res.headers["Content-Encoding"]
                res_obj = module.ResponseObject(res)
                res.headers["Content-Length"] = str(res_obj.size())
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
            if "Content-Encoding" in res.headers:
                del res.headers["Content-Encoding"]
            content_size = os.path.getsize(
                    f"contents/{host}{headers['url']}{suffix}")
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
                 client,
                 recvobj,
                 target,
                 headers):
        res = self.request(target, headers, recvobj)
        if "Transfer-Encoding" in res.headers:
            del res.headers["Transfer-Encoding"]
        host = target.split(":")
        self.response(client, res, host, headers)
        if res.headers.get("Connection") == "close":
            return False
        return True

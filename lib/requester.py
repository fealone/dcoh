import os
import shutil

from lib import payload, rwsocket

import requests


class Requester(object):

    def __init__(self):
        self.session = requests.Session()

    def request(self, target, headers, recvobj, secure=False):
        if secure:
            protocol = "https"
        else:
            protocol = "http"
        host = target.split(":")[0]
        err_count = 0
        if "content-length" in headers["header"]:
            for i in range(3):
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
                    break
                except Exception as e:
                    err_count += 1
                    err = e
                if err_count == 3:
                    raise err
        else:
            for i in range(3):
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
                    break
                except Exception as e:
                    err_count += 1
                    err = e
                if err_count == 3:
                    raise err
        return res

    def response(self, client, res, host, headers):
        rw_client = rwsocket.RWSocket(client)
        suffix = ""
        if headers["url"].endswith("/"):
            suffix = "index.html"
        if os.path.exists(f"contents/{host}{headers['url']}{suffix}"):
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
                 headers,
                 secure=False):
        res = self.request(target, headers, recvobj, secure=True)
        if "Transfer-Encoding" in res.headers:
            del res.headers["Transfer-Encoding"]
        host = target.split(":")
        self.response(client, res, host, headers)
        if res.headers.get("Connection") == "close":
            return False
        return True

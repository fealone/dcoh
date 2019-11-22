import logging
import os
import shutil
import socket
import ssl
import threading

from lib import certs, recvline

import requests


METHODS = ["GET",
           "HEAD",
           "POST",
           "PUT",
           "DELETE",
           "CONNECT",
           "OPTIONS",
           "TRACE",
           "PATCH"]

logger = logging.getLogger("proxy")


class PayloadIterator(object):

    def __init__(self, recvobj, size):
        self.recvobj = recvobj
        self.size = size
        self.byte = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.byte == self.size:
            raise StopIteration()
        raw = next(self.recvobj.recv(self.size))
        if raw:
            self.byte += len(raw)
            return raw
        else:
            raise StopIteration()


class Proxy(object):

    def __init__(self, host="127.0.0.1", port=443):
        self.root_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.root_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.root_server.bind((host, port))
        self.root_server.listen(1024)
        self.connections = {}
        self.session = requests.Session()
        self.lock = threading.Lock()

    def header_receive(self, recvobj):
        header = {}
        raw = recvobj.recvline().decode("utf-8")
        if not raw:
            raise Exception("Does not has received data.")
        req_method = raw.split(" ")[0]
        headers = {}
        if req_method not in METHODS:
            raise Exception("Corrupted request")
        req_headers = raw.split(" ")
        headers["method"] = req_headers[0]
        headers["url"] = req_headers[1]
        headers["protocol"] = req_headers[2].rstrip()
        while 1:
            raw = recvobj.recvline().decode("utf-8")
            if raw == "\r\n":
                break
            head = raw.split(":")
            key = head[0]
            value = ":".join(head[1:]).strip()
            header[key.lower()] = value
        headers["header"] = header
        return headers

    def websocket_client(self, client, server):
        while 1:
            try:
                raw = client.recv(1024)
                if raw:
                    server.send(raw)
                else:
                    break
            except Exception:
                break
        client.close()
        server.close()

    def websocket_server(self, client, server):
        while 1:
            try:
                raw = server.recv(1024)
                if raw:
                    client.send(raw)
                else:
                    break
            except Exception:
                break
        client.close()
        server.close()

    def websocket(self, client, target, headers):
        host, port = target.split(":")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = ssl.wrap_socket(sock)
        sock.connect((host, int(port)))
        send_header = f"{headers['method']} {headers['url']} HTTP/1.1\r\n"
        send_header += "\r\n".join([f"{key}: {value}"
                                    for key, value
                                    in headers["header"].items()])
        send_header += "\r\n\r\n"
        sock.send(send_header.encode("utf-8"))
        th_srv = threading.Thread(
                target=self.websocket_server, args=(client, sock))
        th_clt = threading.Thread(
                target=self.websocket_client, args=(client, sock))
        th_srv.setDaemon(True)
        th_clt.setDaemon(True)
        th_srv.start()
        th_clt.start()
        th_srv.join()
        th_clt.join()

    def transfer(self, client, target):
        recvobj = recvline.Recvline(client)
        target = target.decode("utf-8")
        host, port = target.split(":")
        while 1:
            try:
                headers = self.header_receive(recvobj)
            except Exception:
                break
            if headers is None:
                break
            if "upgrade" in headers["header"]:
                if headers["header"]["upgrade"] == "websocket":
                    self.websocket(client, target, headers)
                    break
            err_count = 0
            for i in range(3):
                try:
                    if "content-length" in headers["header"]:
                        size = int(headers["header"]["content-length"])
                        req = requests.Request(
                                headers["method"],
                                f"https://{host}{headers['url']}",
                                headers=headers["header"],
                                data=PayloadIterator(
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
                    else:
                        req = requests.Request(
                                headers["method"],
                                f"https://{target}{headers['url']}",
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
                except Exception:
                    err_count += 1
            if err_count == 3:
                break
            if "Transfer-Encoding" in res.headers:
                del res.headers["Transfer-Encoding"]
            client.write = client.send
            suffix = ""
            if headers["url"].endswith("/"):
                suffix = "index.html"
            try:
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
                    client.send(res_headers.encode("utf-8"))
                    f = open(f"contents/{host}{headers['url']}{suffix}", "rb")
                    hole = open("/dev/null", "ab")
                    shutil.copyfileobj(f, client)
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
                    client.send(res_headers.encode("utf-8"))
                    shutil.copyfileobj(res.raw, client)
            except Exception:
                break
            if res.headers.get("Connection") == "close":
                break
        client.close()

    def worker(self, index, client):
        raw = client.recv(1024)
        header = raw.split(b"\r\n")[0]
        if not header.startswith(b"CONNECT"):
            client.close()
            del self.connections[index]
            return
        target = header.split(b" ")[1]
        host, port = target.split(b":")
        host = host.decode("utf-8")
        err_count = 0
        for i in range(3):
            try:
                self.lock.acquire()
                certs.create_cert(host)
                break
            except Exception:
                err_count += 1
            finally:
                self.lock.release()
        if err_count == 3:
            raise Exception("Failed create certificate")
        client.send(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        err_count = 0
        for i in range(3):
            try:
                client = ssl.wrap_socket(
                        client,
                        keyfile="CA/demoCA/private/cakey.pem",
                        certfile=f"CA/certs/{host}.crt",
                        server_side=True)
                break
            except Exception:
                try:
                    self.lock.acquire()
                    certs.refresh_cert(host)
                    client.close()
                    del self.connections[index]
                    logger.error(f"Failed to create the connection of SSL"
                                 f"to {target}")
                except Exception:
                    pass
                finally:
                    self.lock.release()
                return
        try:
            self.transfer(client, target)
        except Exception as e:
            raise e
        finally:
            del self.connections[index]

    def run(self):
        index = 0
        while 1:
            client, addr = self.root_server.accept()
            th = threading.Thread(target=self.worker, args=(index, client))
            th.setDaemon(True)
            th.start()
            self.connections[index] = th
            index += 1
